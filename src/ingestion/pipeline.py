"""
Document ingestion pipeline.

Orchestrates the full flow: file upload → parsing → chunking → embedding → vector storage.
Designed for both interactive (Streamlit upload) and batch processing.
"""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

from src.ingestion.parsers import parse_document, ParsedDocument
from src.ingestion.chunker import (
    chunk_text,
    chunk_document_parent_child,
    Chunk,
    SectionGroup,
    extract_manual_metadata,
)
from src.llm.base import BaseEmbeddingProvider
from src.vectorstore.base import BaseVectorStore

logger = logging.getLogger(__name__)


@dataclass
class IngestionResult:
    """Summary of a document ingestion operation."""
    filename: str
    file_type: str
    total_pages: int
    total_chunks: int
    status: str  # "success", "error", "skipped"
    error_message: str = ""


class IngestionPipeline:
    """
    End-to-end document ingestion pipeline.

    Takes uploaded files, parses them, chunks the text, generates embeddings,
    and stores everything in the vector database.
    """

    def __init__(
        self,
        embedding_provider: BaseEmbeddingProvider,
        vector_store: BaseVectorStore,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        raw_storage_dir: str | Path = "./data/raw",
        use_parent_child: bool = True,
        child_size_words: int = 250,
        child_overlap_words: int = 50,
        parent_max_words: int = 2000,
    ):
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.raw_storage_dir = Path(raw_storage_dir)
        self.raw_storage_dir.mkdir(parents=True, exist_ok=True)
        self.use_parent_child = use_parent_child
        self.child_size_words = child_size_words
        self.child_overlap_words = child_overlap_words
        self.parent_max_words = parent_max_words

    def ingest_file(self, file_path: Path, document_id: str | None = None) -> IngestionResult:
        """
        Process a single file through the full ingestion pipeline.

        Args:
            file_path: Path to the source document.
            document_id: Optional UUID string for PostgresVectorStore (injected into chunk metadata).

        Returns:
            IngestionResult with status and statistics.
        """
        logger.info(f"Starting ingestion: {file_path.name}")

        try:
            # 1. Parse the document
            parsed = parse_document(file_path)
            if not parsed.pages:
                return IngestionResult(
                    filename=parsed.filename,
                    file_type=parsed.file_type,
                    total_pages=0,
                    total_chunks=0,
                    status="skipped",
                    error_message="No text content found in document.",
                )

            # 2. Chunk (parent-child or flat)
            if self.use_parent_child and document_id and hasattr(self.vector_store, "add_parents"):
                _dummy_chunks, metadatas, chunk_texts = self._chunk_and_store_parents(
                    parsed, document_id
                )
                if not chunk_texts:
                    return IngestionResult(
                        filename=parsed.filename,
                        file_type=parsed.file_type,
                        total_pages=parsed.total_pages,
                        total_chunks=0,
                        status="skipped",
                        error_message="No chunks generated from document.",
                    )
                # Embed with heading prefix for better recall; store/display unchanged child text
                doc_title = parsed.filename
                embedding_texts = [
                    f"{doc_title} | {meta.get('section_path') or 'Document'}\n{child_text}"
                    for meta, child_text in zip(metadatas, chunk_texts)
                ]
                embeddings = self._generate_embeddings(embedding_texts)
                self.vector_store.add_documents(
                    texts=chunk_texts,
                    embeddings=embeddings,
                    metadatas=metadatas,
                )
            else:
                all_chunks = self._chunk_document(parsed)
                if not all_chunks:
                    return IngestionResult(
                        filename=parsed.filename,
                        file_type=parsed.file_type,
                        total_pages=parsed.total_pages,
                        total_chunks=0,
                        status="skipped",
                        error_message="No chunks generated from document.",
                    )
                chunk_texts = [c.text for c in all_chunks]
                embeddings = self._generate_embeddings(chunk_texts)
                metadatas = [dict(c.metadata) for c in all_chunks]
                if document_id:
                    for i, m in enumerate(metadatas):
                        m["document_id"] = document_id
                        m["chunk_index"] = m.get("chunk_index", i)
                self.vector_store.add_documents(
                    texts=chunk_texts,
                    embeddings=embeddings,
                    metadatas=metadatas,
                )

            # 5. Copy source file to raw storage
            dest = self.raw_storage_dir / file_path.name
            if not dest.exists():
                shutil.copy2(str(file_path), str(dest))

            num_chunks = len(chunk_texts) if self.use_parent_child and hasattr(self.vector_store, "add_parents") else len(all_chunks)
            logger.info(
                f"Ingestion complete: {file_path.name} → "
                f"{parsed.total_pages} pages, {num_chunks} chunks"
            )

            return IngestionResult(
                filename=parsed.filename,
                file_type=parsed.file_type,
                total_pages=parsed.total_pages,
                total_chunks=num_chunks,
                status="success",
            )

        except Exception as e:
            logger.error(f"Ingestion failed for {file_path.name}: {e}")
            return IngestionResult(
                filename=file_path.name,
                file_type=file_path.suffix.lstrip("."),
                total_pages=0,
                total_chunks=0,
                status="error",
                error_message=str(e),
            )

    def ingest_batch(self, file_paths: list[Path]) -> list[IngestionResult]:
        """Process multiple files through the ingestion pipeline."""
        results = []
        for path in file_paths:
            result = self.ingest_file(path)
            results.append(result)
        return results

    def _chunk_and_store_parents(
        self, parsed: ParsedDocument, document_id: str | None
    ) -> tuple[list[Chunk], list[dict], list[str]]:
        """Build parent-child groups, insert parents, return (dummy_chunks, metadatas, child_texts)."""
        if not document_id:
            raise ValueError("document_id required for parent-child ingestion")
        groups = chunk_document_parent_child(
            parsed.pages,
            source_name=parsed.filename,
            file_type=parsed.file_type,
            child_size=self.child_size_words,
            child_overlap=self.child_overlap_words,
            parent_max_words=self.parent_max_words,
            use_words=True,
        )
        parent_records = [
            {
                "section_path": g.section_path,
                "text_parent": g.parent_text,
                "page_start": g.page_start,
                "page_end": g.page_end,
                "metadata": g.base_metadata,
            }
            for g in groups
        ]
        parent_ids = self.vector_store.add_parents(document_id, parent_records)
        metadatas = []
        child_texts = []
        chunk_index = 0
        for g, parent_id in zip(groups, parent_ids):
            for j, child_text in enumerate(g.child_texts):
                extracted = extract_manual_metadata(child_text)
                meta = {
                    **g.base_metadata,
                    "document_id": document_id,
                    "chunk_index": chunk_index,
                    "section_path": g.section_path,
                    "section": g.section_path,  # for citation [source|p=N|s=...]
                    "page_start": g.page_start,
                    "page_end": g.page_end,
                    "content_type": g.content_type,
                    "parent_id": parent_id,
                    "part_numbers": extracted.get("part_numbers"),
                    "error_codes": extracted.get("error_codes"),
                    "model_number": extracted.get("model_number"),
                }
                metadatas.append(meta)
                child_texts.append(child_text)
                chunk_index += 1
        dummy = [Chunk(text=t, chunk_index=i, metadata=m) for i, (t, m) in enumerate(zip(child_texts, metadatas))]
        return dummy, metadatas, child_texts

    def _chunk_document(self, parsed: ParsedDocument) -> list[Chunk]:
        """Chunk all pages of a parsed document."""
        all_chunks = []
        for page in parsed.pages:
            base_metadata = {
                "source": parsed.filename,
                "file_type": parsed.file_type,
                **page.metadata,
            }
            chunks = chunk_text(
                text=page.text,
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                metadata=base_metadata,
            )
            all_chunks.extend(chunks)
        return all_chunks

    def _generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings in batches to respect API limits."""
        batch_size = 100  # OpenAI supports up to 2048, but smaller is safer
        all_embeddings: list[list[float]] = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            embeddings = self.embedding_provider.embed_batch(batch)
            all_embeddings.extend(embeddings)
            logger.debug(f"Embedded batch {i // batch_size + 1}: {len(batch)} chunks")

        return all_embeddings
