"""
Minimal baseline RAG path: light query normalization + vector-only retrieval.

No hybrid, rerank, query rewrite, two-pass, or abstain. Used when use_baseline_path
or RAG_FORCE_BASELINE=1. See docs/RAG_PIPELINE_MAP.md and RAG_RESET_IMPLEMENTATION_PLAN.md.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from src.vectorstore.base import SearchResult

if TYPE_CHECKING:
    from src.llm.base import BaseEmbeddingProvider
    from src.vectorstore.base import BaseVectorStore


def normalize_query(question: str) -> str:
    """Light normalization only: strip and collapse whitespace. No profile/entity/lexical rewrite."""
    if not question or not isinstance(question, str):
        return ""
    return re.sub(r"\s+", " ", question.strip()).strip()


def run_baseline_retrieval(
    embedder: "BaseEmbeddingProvider",
    vector_store: "BaseVectorStore",
    query: str,
    top_k: int,
) -> list[SearchResult]:
    """
    Vector-only retrieval: embed query, search, return top_k in order.
    Optionally dedupe by short text prefix (keep first occurrence).
    """
    if not query.strip():
        return []
    embedding = embedder.embed_text(query)
    results = vector_store.search(
        query_embedding=embedding,
        top_k=top_k * 2,
        metadata_filter=None,
    )
    if not results:
        return []
    deduped = _dedupe_by_prefix(results, prefix_len=120)
    return deduped[:top_k]


def _dedupe_by_prefix(
    results: list[SearchResult],
    prefix_len: int = 120,
) -> list[SearchResult]:
    """Keep first occurrence of each normalized text prefix. Deterministic order."""
    seen: set[str] = set()
    out: list[SearchResult] = []
    for r in results:
        prefix = (r.text[:prefix_len] + "..").strip().lower()
        if prefix in seen:
            continue
        seen.add(prefix)
        out.append(r)
    return out
