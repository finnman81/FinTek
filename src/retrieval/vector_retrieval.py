"""
Vector retrieval logic extracted from RetrievalEngine.

Handles hybrid/dense search, metadata filtering, and query text construction.
"""

from __future__ import annotations

import re
from typing import Any

import structlog

from src.retrieval.query_rewrite import extract_query_entities
from src.vectorstore.base import BaseVectorStore, SearchResult

logger = structlog.get_logger()


def build_metadata_filter(question: str) -> dict[str, Any] | None:
    """Build a metadata filter dict from entities detected in the question."""
    entities = extract_query_entities(question)
    filt: dict[str, Any] = {}
    if entities.get("error_codes"):
        filt["error_codes"] = entities["error_codes"]
    if entities.get("part_numbers"):
        filt["part_numbers"] = entities["part_numbers"]
    return filt or None


def build_retrieval_query_text(
    question: str,
    entity_filter: dict[str, Any] | None,
    profile: str,
) -> str:
    """Use entity-focused lexical query for code/part lookups to avoid lexical miss-rate."""
    if profile not in {"error_codes", "spec_lookup"} or not entity_filter:
        return question
    parts = (entity_filter.get("error_codes") or []) + (
        entity_filter.get("part_numbers") or []
    )
    compact = [p.strip() for p in parts if isinstance(p, str) and p.strip()]
    return " ".join(compact) if compact else question


def profile_params(
    profile: str,
    *,
    top_k: int,
    vector_top_k: int,
    lexical_top_k: int,
    final_k: int,
) -> dict[str, int]:
    """Return retrieval parameters adjusted for the given query profile."""
    params = {
        "top_k": top_k,
        "vector_top_k": vector_top_k,
        "lexical_top_k": lexical_top_k,
        "final_k": final_k,
    }
    if profile in {"error_codes", "spec_lookup"}:
        params["vector_top_k"] = max(20, vector_top_k - 10)
        params["lexical_top_k"] = lexical_top_k + 10
        params["final_k"] = max(8, final_k - 4)
        params["top_k"] = max(5, top_k - 1)
    elif profile in {"procedures", "troubleshooting"}:
        params["vector_top_k"] = vector_top_k + 10
        params["final_k"] = final_k
    return params


def retrieve(
    question: str,
    query_embedding: list[float],
    metadata_filter: dict[str, Any] | None,
    *,
    vector_store: BaseVectorStore,
    use_hybrid: bool,
    rrf_k: int,
    ef_search: int,
    params: dict[str, int],
    query_text_alt: str | None = None,
) -> list[SearchResult]:
    """Run hybrid or dense-only retrieval."""
    if use_hybrid and hasattr(vector_store, "search_hybrid"):
        return vector_store.search_hybrid(
            query_text=question,
            query_embedding=query_embedding,
            vector_top_k=params["vector_top_k"],
            lexical_top_k=params["lexical_top_k"],
            rrf_k=rrf_k,
            final_k=params["final_k"],
            ef_search=ef_search,
            metadata_filter=metadata_filter,
            query_text_alt=query_text_alt,
        )
    return vector_store.search(
        query_embedding=query_embedding,
        top_k=params["top_k"],
        metadata_filter=metadata_filter,
    )


def retrieve_with_debug(
    question: str,
    query_embedding: list[float],
    metadata_filter: dict[str, Any] | None,
    *,
    vector_store: BaseVectorStore,
    use_hybrid: bool,
    rrf_k: int,
    ef_search: int,
    params: dict[str, int],
    include_debug: bool = False,
    query_text_alt: str | None = None,
) -> tuple[list[SearchResult], dict[str, Any]]:
    """Retrieve results and, when available, retrieval stage debug details."""
    debug: dict[str, Any] = {}
    if use_hybrid and hasattr(vector_store, "search_hybrid_with_debug"):
        results, hybrid_debug = vector_store.search_hybrid_with_debug(
            query_text=question,
            query_embedding=query_embedding,
            vector_top_k=params["vector_top_k"],
            lexical_top_k=params["lexical_top_k"],
            rrf_k=rrf_k,
            final_k=params["final_k"],
            ef_search=ef_search,
            metadata_filter=metadata_filter,
            include_debug=include_debug,
            query_text_alt=query_text_alt,
        )
        return results, hybrid_debug or {}

    results = retrieve(
        question,
        query_embedding,
        metadata_filter,
        vector_store=vector_store,
        use_hybrid=use_hybrid,
        rrf_k=rrf_k,
        ef_search=ef_search,
        params=params,
        query_text_alt=query_text_alt,
    )
    if include_debug and not use_hybrid:
        debug["vector_hits"] = [{"id": r.document_id, "score": r.score} for r in results]
    return results, debug

# ---------------------------------------------------------------------------
# Fin-Tek retrieval boosting (Req 19.1, 19.2)
# ---------------------------------------------------------------------------

_MODEL_NUMBER_RE = re.compile(r'\bM4[6-8][05][HLM]?\b|\b[34][35]50\b', re.IGNORECASE)

_TROUBLESHOOTING_KEYWORDS = frozenset([
    "troubleshoot", "troubleshooting", "error", "fault", "symptom",
    "not working", "diagnostic", "diagnose", "failure",
])

_MAINTENANCE_KEYWORDS = frozenset([
    "pm", "maintenance", "preventive", "schedule", "scheduled",
    "procedure", "calibration", "inspection",
])

_PARTS_SPEC_KEYWORDS = frozenset([
    "parts", "part", "spec", "specification", "specifications",
    "bom", "bill of materials", "component", "components",
])


def boost_model_number_query(
    question: str,
    results: list[SearchResult],
    *,
    model_number_boost: float = 1.3,
) -> list[SearchResult]:
    """Boost chunks whose model_number matches a model number found in the query.

    Applies the configured ``model_number_boost`` multiplier to matching chunks
    and re-sorts by score descending.
    """
    query_models = [m.upper() for m in _MODEL_NUMBER_RE.findall(question)]
    if not query_models:
        return results
    for r in results:
        chunk_model = (r.metadata.get("model_number") or "").upper()
        if chunk_model and chunk_model in query_models:
            r.score *= model_number_boost
            logger.debug(
                "model_number_boost applied",
                chunk_id=r.document_id,
                model=chunk_model,
                boost=model_number_boost,
            )
    return sorted(results, key=lambda r: r.score, reverse=True)


def _query_has_keywords(question: str, keywords: frozenset[str]) -> bool:
    """Return True if *question* contains any of the given keywords."""
    q_lower = question.lower()
    return any(kw in q_lower for kw in keywords)


def boost_content_type(
    question: str,
    results: list[SearchResult],
    *,
    content_type_boost: float = 1.3,
) -> list[SearchResult]:
    """Boost chunks based on query keywords matching content types.

    * Troubleshooting keywords → boost ``troubleshooting_tree`` chunks.
    * Maintenance keywords → boost ``pm_procedure`` chunks.
    * Parts/spec keywords → boost ``parts_list`` chunks.
    """
    boost_type: str | None = None
    if _query_has_keywords(question, _TROUBLESHOOTING_KEYWORDS):
        boost_type = "troubleshooting_tree"
    elif _query_has_keywords(question, _MAINTENANCE_KEYWORDS):
        boost_type = "pm_procedure"
    elif _query_has_keywords(question, _PARTS_SPEC_KEYWORDS):
        boost_type = "parts_list"

    if boost_type is None:
        return results

    for r in results:
        if r.metadata.get("content_type") == boost_type:
            r.score *= content_type_boost
            logger.debug(
                "content_type_boost applied",
                chunk_id=r.document_id,
                content_type=boost_type,
                boost=content_type_boost,
            )
    return sorted(results, key=lambda r: r.score, reverse=True)

