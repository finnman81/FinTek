"""
Manual-focused query rewriting for retrieval.

Produces literal (code-preserving), semantic, and procedure-phrasing variants
so dense + lexical can pick up part numbers, error codes, and "how to" questions.
"""

from __future__ import annotations

import re
from typing import Any

ERROR_CODE_RE = re.compile(r"\b(?:E\d{2,4}|ERR[- ]?\d+|F\d{2,4}|ALARM\d+)\b", re.IGNORECASE)
PART_NUMBER_RE = re.compile(r"\b(?:[A-Z]-\d{2,6}|[A-Z]{1,4}\d{2,8}|\d{4,8}[A-Z0-9-]*)\b", re.IGNORECASE)

# Procedure/symptom phrasing prefixes for manual-style questions
PROCEDURE_PREFIXES = (
    "how to replace ",
    "how to install ",
    "how to troubleshoot ",
    "how do i ",
    "steps to ",
    "procedure for ",
    "troubleshoot ",
    "replace ",
    "install ",
    "repair ",
)


def get_rewrite_variants(question: str, max_variants: int = 5) -> list[str]:
    """
    Return 3–5 query variants for hybrid retrieval.

    - literal: keep original (preserves part numbers, error codes).
    - semantic: optional expansion (e.g. "E04" -> "error E04").
    - procedure: rephrase as "how to ..." / "troubleshoot ..." when appropriate.

    Returns:
        List of query strings; first is always the original.
    """
    q = question.strip()
    if not q:
        return [q]
    seen = {q.lower()}
    variants = [q]

    # Procedure phrasing: if question looks like a symptom or part, add "how to troubleshoot X" / "steps for X"
    lower = q.lower()
    if not any(lower.startswith(p) for p in PROCEDURE_PREFIXES):
        procedure = f"how to troubleshoot {q}" if len(q) < 80 else q
        if procedure.lower() not in seen:
            seen.add(procedure.lower())
            variants.append(procedure)
    if len(variants) >= max_variants:
        return variants[:max_variants]

    # Literal reinforcement: if query has codes/numbers, add a short "procedure for X" variant
    if re.search(r"\b(?:E\d{2,4}|ERR|part\s*#?|model\s*#?)\b", q, re.IGNORECASE):
        literal_proc = f"procedure for {q}" if len(q) < 70 else q
        if literal_proc.lower() not in seen:
            seen.add(literal_proc.lower())
            variants.append(literal_proc)
    return variants[:max_variants]


def detect_numeric_intent(question: str) -> bool:
    """True if the question likely asks for specs, numbers, or tables."""
    lower = question.lower()
    return any(
        w in lower
        for w in (
            "spec", "specification", "rating", "pressure", "flow", "capacity",
            "size", "dimension", "torque", "voltage", "psi", "gpm", "table",
            "number", "value", "setting", "parameter",
        )
    )


def detect_query_profile(question: str) -> str:
    """Coarse intent profile used to apply retrieval presets."""
    q = (question or "").lower()
    if re.search(ERROR_CODE_RE, question or "") or "error code" in q or "fault code" in q or "part number" in q:
        return "error_codes"
    if any(w in q for w in ("safety", "hazard", "warning", "ppe", "lockout", "tagout")):
        return "safety"
    if any(w in q for w in ("install", "procedure", "steps", "setup", "startup", "configure")):
        return "procedures"
    if any(w in q for w in ("not starting", "overheating", "leaking", "troubleshoot", "problem")):
        return "troubleshooting"
    if detect_numeric_intent(question):
        return "spec_lookup"
    return "general"


def extract_query_entities(question: str) -> dict[str, list[str]]:
    """Extract manual entities that can be used for metadata-aware filtering."""
    q = question or ""
    return {
        "error_codes": sorted({m.upper() for m in ERROR_CODE_RE.findall(q)}),
        "part_numbers": sorted({m.upper() for m in PART_NUMBER_RE.findall(q)}),
    }


_MODEL_PART_TOKEN_RE = re.compile(r"\b([A-Za-z]{1,4})([-\s]?)(\d{2,8})\b")


def generate_lexical_alt(query: str) -> str:
    """Flip model/part token forms so FTS can match either variant.

    SC200 → SC 200  (matches docs tokenised as SC-200 → 'sc','200')
    SC-200 → SC200  (matches docs tokenised as SC200 → 'sc200')
    """
    def _flip(m: re.Match) -> str:
        letters, sep, digits = m.group(1), m.group(2), m.group(3)
        if sep:
            return f"{letters}{digits}"
        return f"{letters} {digits}"

    alt = _MODEL_PART_TOKEN_RE.sub(_flip, query)
    return alt if alt != query else query


def is_safety_chunk(metadata: dict[str, Any]) -> bool:
    """True if chunk is a warning/safety type."""
    ct = (metadata.get("content_type") or "").lower()
    section = (metadata.get("section_path") or metadata.get("section") or "").lower()
    return ct == "warning" or "warning" in section or "safety" in section or "caution" in section


def is_spec_or_table_chunk(metadata: dict[str, Any]) -> bool:
    """True if chunk is spec or table content."""
    ct = (metadata.get("content_type") or "").lower()
    return ct in ("spec", "table")
