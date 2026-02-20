"""
ChromaDB implementation of the vector store.

Stores embeddings locally on disk with zero infrastructure requirements.
Ideal for MVP / single-tenant deployments.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings

from src.vectorstore.base import BaseVectorStore, SearchResult

logger = logging.getLogger(__name__)


class ChromaVectorStore(BaseVectorStore):
    """Local ChromaDB vector store with file-based persistence."""

    def __init__(
        self,
        collection_name: str = "documents",
        persist_directory: str = "./data/processed/chroma",
        distance_metric: str = "cosine",
    ):
        persist_path = Path(persist_directory)
        persist_path.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(persist_path),
            settings=Settings(anonymized_telemetry=False),
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": distance_metric},
        )

        logger.info(
            f"ChromaDB initialized: collection='{collection_name}', "
            f"documents={self.collection.count()}, path='{persist_directory}'"
        )

    def add_documents(
        self,
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
    ) -> list[str]:
        if not texts:
            return []

        doc_ids = ids or [str(uuid.uuid4()) for _ in texts]
        metadatas = metadatas or [{} for _ in texts]

        # ChromaDB requires metadata values to be str, int, float, or bool
        sanitized_metadatas = []
        for meta in metadatas:
            sanitized = {}
            for k, v in meta.items():
                if isinstance(v, (str, int, float, bool)):
                    sanitized[k] = v
                else:
                    sanitized[k] = str(v)
            sanitized_metadatas.append(sanitized)

        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=sanitized_metadatas,
            ids=doc_ids,
        )

        logger.info(f"Added {len(texts)} documents to ChromaDB")
        return doc_ids

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        query_params: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": min(top_k, self.collection.count()) if self.collection.count() > 0 else top_k,
            "include": ["documents", "metadatas", "distances"],
        }

        if metadata_filter:
            query_params["where"] = metadata_filter

        if self.collection.count() == 0:
            return []

        results = self.collection.query(**query_params)

        search_results = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        ids = results.get("ids", [[]])[0]

        for doc, meta, dist, doc_id in zip(documents, metadatas, distances, ids):
            # ChromaDB returns distances; convert to similarity score
            # For cosine distance: similarity = 1 - distance
            score = 1.0 - dist

            search_results.append(
                SearchResult(
                    text=doc,
                    score=score,
                    metadata=meta or {},
                    document_id=doc_id,
                )
            )

        return search_results

    def delete(self, ids: list[str]) -> None:
        if ids:
            self.collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents from ChromaDB")

    def count(self) -> int:
        return self.collection.count()

    def clear(self) -> None:
        # ChromaDB doesn't have a clear method; delete and recreate
        collection_name = self.collection.name
        metadata = self.collection.metadata
        self.client.delete_collection(collection_name)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata=metadata,
        )
        logger.info(f"Cleared collection '{collection_name}'")
