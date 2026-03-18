"""
Abstention logic extracted from RetrievalEngine.

Determines when the engine should decline to answer (abstain) based on
retrieval score thresholds, and handles salvage attempts for false abstentions.
"""

from __future__ import annotations

import re
from typing import Any

import structlog

from src.llm.base import BaseLLMProvider, LLMResponse
from src.llm.prompts import (
    build_extract_sentences_messages,
    build_compose_from_extracted_messages,
)
from src.vectorstore.base import SearchResult

logger = structlog.get_logger()

_ABSTAIN_MARKERS = (
    "not found in provided documents",
    "no relevant passages",
    "not available in the provided context",
    "insufficient information in the provided context",
    "cannot determine from the provided context",
    "i don't have enough information in the provided documents",
    "the provided documents do not contain",
)
_CITATION_PATTERN = re.compile(r"\[[^\]|]+\|(?:p=[^\]|]+|s=[^\]]+)(?:\|s=[^\]]+)?\]")


_VALID_ABSTENTION_MODES = {"score_only", "margin_only", "both", "and"}


def should_abstain(
    results: list[SearchResult],
    abstain_min_top1_score: float,
    abstain_min_margin: float,
    mode: str = "both",
) -> tuple[bool, dict[str, Any]]:
    """Decide whether the engine should abstain from answering.

    Args:
        results: Ranked search results (highest score first).
        abstain_min_top1_score: Minimum acceptable top-1 score.
        abstain_min_margin: Minimum acceptable margin between top-1 and top-2.
        mode: Abstention strategy —
            ``"score_only"``: abstain iff top-1 score < threshold.
            ``"margin_only"``: abstain iff margin < threshold.
            ``"both"`` (default, OR): abstain if *either* condition is met.
            ``"and"``: abstain only if *both* conditions are met.
            Unrecognised values default to ``"both"`` with a warning log.

    Returns:
        (should_abstain, details_dict) where *details_dict* contains
        diagnostic information about the decision.
    """
    if mode not in _VALID_ABSTENTION_MODES:
        logger.warning("Unrecognised abstention mode; defaulting to 'both'", mode=mode)
        mode = "both"

    if not results:
        return True, {"reason": "no_results", "mode": mode}

    top1 = results[0].score
    has_competitor = len(results) > 1
    top2 = results[1].score if has_competitor else None
    margin = (top1 - top2) if has_competitor and top2 is not None else None

    by_score = top1 < abstain_min_top1_score
    by_margin = (margin is not None) and (margin < abstain_min_margin)

    if mode == "score_only":
        decision = by_score
    elif mode == "margin_only":
        decision = by_margin
    elif mode == "and":
        decision = by_score and by_margin
    else:  # "both" (OR)
        decision = by_score or by_margin

    return decision, {
        "top1": top1,
        "top2": top2,
        "margin": margin,
        "has_competitor": has_competitor,
        "min_top1_score": abstain_min_top1_score,
        "min_margin": abstain_min_margin,
        "abstain_by_score": by_score,
        "abstain_by_margin": by_margin,
        "mode": mode,
    }


def is_abstention_answer(answer: str) -> bool:
    """Return True if the answer text looks like an abstention / 'not found' response."""
    if not answer:
        return True
    lower = answer.strip().lower()
    return any(marker in lower for marker in _ABSTAIN_MARKERS)


def salvage_answer_with_extraction(
    question: str,
    context_chunks: list[dict[str, Any]],
    original: LLMResponse,
    llm: BaseLLMProvider,
) -> LLMResponse:
    """Retry via extraction+compose when single-pass answer incorrectly abstains."""
    extract_messages = build_extract_sentences_messages(question, context_chunks)
    extract_response = llm.generate(extract_messages)
    extracted_text = extract_response.content.strip()
    if not _CITATION_PATTERN.search(extracted_text):
        return original

    compose_messages = build_compose_from_extracted_messages(question, extracted_text)
    compose_response = llm.generate(compose_messages)
    if is_abstention_answer(compose_response.content):
        return original

    u1 = extract_response.usage or {}
    u2 = compose_response.usage or {}
    merged_usage = {
        "prompt_tokens": (original.usage or {}).get("prompt_tokens", 0) + u1.get("prompt_tokens", 0) + u2.get("prompt_tokens", 0),
        "completion_tokens": (original.usage or {}).get("completion_tokens", 0) + u1.get("completion_tokens", 0) + u2.get("completion_tokens", 0),
        "total_tokens": (original.usage or {}).get("total_tokens", 0) + u1.get("total_tokens", 0) + u2.get("total_tokens", 0),
    }
    return LLMResponse(
        content=compose_response.content,
        model=compose_response.model,
        usage=merged_usage,
        metadata=compose_response.metadata,
    )


# ---------------------------------------------------------------------------
# LLM-based relevance gate (fallback when reranker scores are unavailable/NaN)
# ---------------------------------------------------------------------------

_RELEVANCE_GATE_PROMPT = """You are a relevance judge for a technical knowledge base about Teledyne ozone and gas monitoring equipment (M460, M465, M480, 3350, 3550 series).

Given the user's question and the top retrieved context snippets, decide: does the context contain information relevant to answering the question?

Rules:
- Answer YES only if the context includes concrete facts, steps, ranges, alarms, parts, or specs that directly support an answer to the question.
- Answer NO if the context is only topically related (same product family/model) but lacks supporting details needed for this specific question.
- Answer NO if the context is entirely about different equipment brands, unrelated topics, or generic text that has no connection to the question.
- Answer NO if the question is about a topic completely outside industrial gas monitoring equipment (e.g., cooking, programming, geography, finance, weather).

Question: {question}

Context (top retrieved chunks):
{context}

Is the context relevant to the question? Reply with ONLY "YES" or "NO"."""


def llm_relevance_gate(
    question: str,
    context_chunks: list[dict[str, Any]],
    llm: BaseLLMProvider,
) -> tuple[bool, str]:
    """Quick LLM check: does the retrieved context actually answer the question?

    Returns:
        (is_relevant, raw_response) — *is_relevant* is True if the LLM says YES.
    """
    # Use first 5 chunks, truncated, to keep the prompt small and fast
    snippets = []
    for i, chunk in enumerate(context_chunks[:5], 1):
        text = (chunk.get("text", "") or "")[:500]
        snippets.append(f"[{i}] {text}")
    context_str = "\n\n".join(snippets) if snippets else "(no context)"

    prompt = _RELEVANCE_GATE_PROMPT.format(question=question, context=context_str)
    try:
        response = llm.generate([{"role": "user", "content": prompt}])
        answer = response.content.strip().upper()
        is_relevant = answer.startswith("YES")
        logger.info("LLM relevance gate: %s (raw=%r)", "relevant" if is_relevant else "not relevant", answer[:20])
        return is_relevant, response.content
    except Exception as e:
        logger.warning("LLM relevance gate failed: %s; defaulting to relevant", e)
        return True, f"error: {e}"
