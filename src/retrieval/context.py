"""
Context assembly logic extracted from RetrievalEngine.

Handles deduplication, reordering (procedure → safety → spec → rest),
formatting, and source extraction for search results.
"""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any

from src.llm.prompts import citation_bracket
from src.retrieval.query_rewrite import (
    detect_numeric_intent,
    is_safety_chunk,
    is_spec_or_table_chunk,
)
from src.vectorstore.base import SearchResult


def _similarity(a: str, b: str) -> float:
    """Ratio of similarity between two strings (0-1)."""
    return SequenceMatcher(None, a.strip().lower(), b.strip().lower()).ratio()


def dedupe_by_similarity(
    results: list[SearchResult], similarity_threshold: float = 0.90
) -> list[SearchResult]:
    """Keep higher-scoring chunk when two are very similar (e.g. 90% same)."""
    if len(results) <= 1:
        return results
    kept: list[SearchResult] = []
    for r in results:
        is_dupe = False
        for k in kept:
            if _similarity(r.text, k.text) >= similarity_threshold:
                is_dupe = True
                break
        if not is_dupe:
            kept.append(r)
    return kept


def assemble_context(
    results: list[SearchResult],
    question: str,
    *,
    keep: int,
) -> list[SearchResult]:
    """Deduplicate (prefix + similarity) and reorder: procedure first, then safety, then spec if numeric."""
    if not results:
        return results
    # 1. Dedupe by normalized text prefix
    seen_prefix: set[str] = set()
    by_prefix: list[SearchResult] = []
    for r in results:
        prefix = (r.text[:120] + "..").strip().lower()
        if prefix in seen_prefix:
            continue
        seen_prefix.add(prefix)
        by_prefix.append(r)
    # 2. Dedupe by high similarity (keep higher score)
    deduped = dedupe_by_similarity(by_prefix, similarity_threshold=0.90)
    # 3. Order: procedure first, then one safety, then one spec if numeric, then rest
    procedure: list[SearchResult] = []
    safety: list[SearchResult] = []
    spec: list[SearchResult] = []
    other: list[SearchResult] = []
    for r in deduped:
        if is_safety_chunk(r.metadata):
            safety.append(r)
        elif is_spec_or_table_chunk(r.metadata):
            spec.append(r)
        elif (r.metadata.get("content_type") or "").lower() == "procedure":
            procedure.append(r)
        else:
            other.append(r)
    numeric = detect_numeric_intent(question)
    out: list[SearchResult] = procedure[:2]
    if safety:
        out.append(safety[0])
    if numeric and spec:
        out.append(spec[0])
    rest = [r for r in deduped if r not in out]
    out.extend(rest)
    return out[:keep]


def format_context(results: list[SearchResult]) -> list[dict]:
    """Format search results into context chunks for the prompt."""
    return [
        {
            "text": f"{citation_bracket(r.metadata)}\n{r.text}",
            "metadata": r.metadata,
            "score": r.score,
        }
        for r in results
    ]


def extract_sources(results: list[SearchResult]) -> list[dict[str, Any]]:
    """Extract unique source documents from search results."""
    seen: set[str] = set()
    sources: list[dict[str, Any]] = []

    for r in results:
        source_name = r.metadata.get("source", "Unknown")
        page = r.metadata.get("page", "") or r.metadata.get("page_start", "")
        section = r.metadata.get("section", "") or r.metadata.get("section_path", "")
        key = f"{source_name}:{page}:{section}"

        if key not in seen:
            seen.add(key)
            sources.append({
                "source": source_name,
                "document": source_name,
                "page": page,
                "section": section,
                "text": r.text,
                "relevance_score": round(r.score, 3),
            })

    return sources
