"""
Abstract base class for vector store implementations.

Supports ChromaDB (local) today, Pinecone/Weaviate tomorrow.
The retrieval engine never touches provider-specific APIs directly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SearchResult:
    """A single result from a vector similarity search."""
    text: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)
    document_id: str = ""
    # When reranker is used, set by engine from reranker output; used for abstain and top1/top3/margin.
    rerank_score: float | None = None


class BaseVectorStore(ABC):
    """Abstract interface for vector storage and retrieval."""

    @abstractmethod
    def add_documents(
        self,
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
    ) -> list[str]:
        """
        Add documents to the vector store.

        Returns:
            List of document IDs that were added.
        """
        ...

    @abstractmethod
    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """
        Search for similar documents by embedding vector.

        Returns:
            List of SearchResult objects sorted by relevance.
        """
        ...

    @abstractmethod
    def delete(self, ids: list[str]) -> None:
        """Delete documents by their IDs."""
        ...

    @abstractmethod
    def count(self) -> int:
        """Return the total number of documents in the store."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Remove all documents from the store."""
        ...

    def add_parents(
        self,
        document_id: str,
        parents: list[dict[str, Any]],
    ) -> list[str]:
        """
        Optional: add parent (section-level) records for parent-child retrieval.
        Default no-op returns []. Override in pgvector store.
        """
        return []
