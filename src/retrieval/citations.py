"""
Citation repair logic extracted from RetrievalEngine.

Ensures every line in an LLM answer has a proper bracket citation.
Non-factual lines (transitional phrases) are left without citations.
Repaired citations are validated against actually-retrieved sources.
"""

from __future__ import annotations

import re

from src.llm.prompts import citation_bracket
from src.vectorstore.base import SearchResult

_CITATION_PATTERN = re.compile(r"\[[^\]|]+\|(?:p=[^\]|]+|s=[^\]]+)(?:\|s=[^\]]+)?\]")

# Lines starting with these prefixes contain no factual claims and should not
# receive a default citation.  Matching is case-insensitive.
_NON_FACTUAL_PREFIXES: list[str] = [
    "based on the documentation",
    "based on the provided",
    "here is the procedure",
    "here are the steps",
    "according to the manual",
    "according to the documentation",
    "the following steps",
    "below is the procedure",
    "as described in the",
    "in summary",
    "to summarize",
    "please note that",
    "note:",
    "for reference",
    "as mentioned",
]


def _is_non_factual(line: str) -> bool:
    """Return True if *line* is a transitional/non-factual phrase."""
    lower = line.lower().strip()
    return any(lower.startswith(prefix) for prefix in _NON_FACTUAL_PREFIXES)


def _retrieved_source_names(results: list[SearchResult]) -> set[str]:
    """Extract the set of source document names from retrieved results."""
    names: set[str] = set()
    for r in results:
        src = r.metadata.get("source", "")
        if src:
            names.add(src.lower().strip())
    return names


def _citation_references_retrieved_source(
    citation_text: str,
    retrieved_sources: set[str],
) -> bool:
    """Check whether a citation bracket references a retrieved source."""
    # Extract the source portion from [source|p=N|s=...]
    match = re.match(r"\[([^|\]]+)", citation_text)
    if not match:
        return False
    cite_source = match.group(1).lower().strip()
    for src in retrieved_sources:
        if cite_source == src or cite_source.endswith(src) or src.endswith(cite_source):
            return True
    return False


def repair_missing_citations(
    answer: str,
    results: list[SearchResult],
    retrieved_sources: set[str] | None = None,
) -> str:
    """Append the top-result citation to any factual line that lacks one.

    Non-factual lines (transitional phrases) are left without citations.
    If *retrieved_sources* is provided, existing citations that reference
    a source not in the retrieved set are replaced with the top-result citation.
    """
    if not answer or not results:
        return answer

    top_citation = citation_bracket(results[0].metadata)
    if retrieved_sources is None:
        retrieved_sources = _retrieved_source_names(results)

    lines = [ln.strip() for ln in answer.split("\n") if ln.strip()]
    repaired: list[str] = []

    for ln in lines:
        existing = _CITATION_PATTERN.search(ln)
        if existing:
            # Validate existing citation references a retrieved source
            if _citation_references_retrieved_source(existing.group(), retrieved_sources):
                repaired.append(ln)
            else:
                # Replace hallucinated citation with top-result citation
                cleaned = _CITATION_PATTERN.sub("", ln).rstrip()
                if _is_non_factual(cleaned):
                    repaired.append(cleaned)
                else:
                    repaired.append(f"{cleaned} {top_citation}")
        elif _is_non_factual(ln):
            # Non-factual line — no citation appended
            repaired.append(ln)
        else:
            repaired.append(f"{ln.rstrip('.')} {top_citation}")

    return "\n".join(repaired)
