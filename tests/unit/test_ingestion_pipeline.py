"""
Unit tests for IngestionPipeline with mocked embedding provider and vector store.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.ingestion.pipeline import IngestionPipeline, IngestionResult
from src.ingestion.parsers import ParsedDocument, ParsedPage
from src.llm.base import BaseEmbeddingProvider
from src.vectorstore.base import BaseVectorStore


def _make_mock_embedder(dim: int = 1536):
    embedder = MagicMock(spec=BaseEmbeddingProvider)
    embedder.embed_batch.return_value = [[0.0] * dim]
    embedder.dimensions = dim
    return embedder


def _make_mock_vector_store():
    store = MagicMock(spec=BaseVectorStore)
    store.add_documents.return_value = ["id1"]
    store.search.return_value = []
    store.count.return_value = 0
    return store


class TestIngestionPipelineIngestFile:
    def test_ingest_txt_file_success(self, tmp_path: Path):
        (tmp_path / "doc.txt").write_text("Hello world. This is content for chunking.")
        embedder = _make_mock_embedder()
        store = _make_mock_vector_store()
        pipeline = IngestionPipeline(
            embedding_provider=embedder,
            vector_store=store,
            chunk_size=1000,
            chunk_overlap=0,
            raw_storage_dir=tmp_path / "raw",
        )
        result = pipeline.ingest_file(tmp_path / "doc.txt")
        assert isinstance(result, IngestionResult)
        assert result.status == "success"
        assert result.total_chunks >= 1
        assert result.filename == "doc.txt"
        store.add_documents.assert_called_once()
        assert embedder.embed_batch.called

    def test_ingest_empty_txt_returns_skipped(self, tmp_path: Path):
        (tmp_path / "empty.txt").write_text("   \n\t  ")
        pipeline = IngestionPipeline(
            embedding_provider=_make_mock_embedder(),
            vector_store=_make_mock_vector_store(),
            raw_storage_dir=tmp_path / "raw",
        )
        result = pipeline.ingest_file(tmp_path / "empty.txt")
        assert result.status == "skipped"
        assert result.total_chunks == 0
        assert "No text" in result.error_message or "No chunks" in result.error_message

    def test_ingest_with_document_id_injects_into_metadata(self, tmp_path: Path):
        (tmp_path / "x.txt").write_text("Some content here.")
        store = _make_mock_vector_store()
        pipeline = IngestionPipeline(
            embedding_provider=_make_mock_embedder(),
            vector_store=store,
            raw_storage_dir=tmp_path / "raw",
        )
        doc_id = "550e8400-e29b-41d4-a716-446655440000"
        result = pipeline.ingest_file(tmp_path / "x.txt", document_id=doc_id)
        assert result.status == "success"
        call_kw = store.add_documents.call_args[1]
        metadatas = call_kw.get("metadatas") or []
        assert all(m.get("document_id") == doc_id for m in metadatas)

    def test_ingest_nonexistent_file_returns_error(self):
        pipeline = IngestionPipeline(
            embedding_provider=_make_mock_embedder(),
            vector_store=_make_mock_vector_store(),
            raw_storage_dir=Path("/tmp"),
        )
        result = pipeline.ingest_file(Path("/nonexistent/file.txt"))
        assert result.status == "error"
        assert result.error_message

    def test_ingest_unsupported_extension_returns_error(self, tmp_path: Path):
        (tmp_path / "x.xyz").write_text("data")
        pipeline = IngestionPipeline(
            embedding_provider=_make_mock_embedder(),
            vector_store=_make_mock_vector_store(),
            raw_storage_dir=tmp_path / "raw",
        )
        result = pipeline.ingest_file(tmp_path / "x.xyz")
        assert result.status == "error"
        assert "Unsupported" in result.error_message or "Error" in result.error_message
