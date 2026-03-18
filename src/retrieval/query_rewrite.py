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
    if re.search(ERROR_CODE_RE, question or "") or "error code" in q or "fault code" in q or "alarm" in q:
        return "error_codes"
    if "part number" in q or "replacement part" in q:
        return "parts_lookup"
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
    error_codes = sorted({m.upper() for m in ERROR_CODE_RE.findall(q)})
    error_code_set = {code.upper() for code in error_codes}
    part_numbers = sorted(
        {
            m.upper()
            for m in PART_NUMBER_RE.findall(q)
            # Avoid polluting part-number filters with error/fault/alarm codes.
            if m.upper() not in error_code_set
            and not ERROR_CODE_RE.fullmatch(m.upper())
        }
    )
    return {
        "error_codes": error_codes,
        "part_numbers": part_numbers,
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


# ── Query rewriting: model number normalization ─────────────────────

# Canonical Teledyne model numbers: 3-digit get M prefix, 4-digit stay bare
_THREE_DIGIT_MODELS = {"460", "465", "480", "450"}
_FOUR_DIGIT_MODELS = {"3350", "3550"}
_ALL_MODEL_DIGITS = _THREE_DIGIT_MODELS | _FOUR_DIGIT_MODELS

# Matches "Model 465", "Model #3350", "model#465H", case-insensitive
_MODEL_PREFIX_RE = re.compile(
    r"\bmodel\s*#?\s*(\d{3,4})([A-Za-z]*)\b",
    re.IGNORECASE,
)
# Matches bare "M465", "M465H" (already canonical for 3-digit)
_M_PREFIX_RE = re.compile(
    r"\bM(\d{3})([A-Za-z]*)\b",
)
# Matches bare 3-digit with optional suffix like "465H", "460"
_BARE_THREE_DIGIT_RE = re.compile(
    r"\b(\d{3})([HhLlMm]?)\b",
)
# Matches bare 4-digit like "3350", "3550"
_BARE_FOUR_DIGIT_RE = re.compile(
    r"\b(\d{4})([A-Za-z]*)\b",
)


def normalize_model_number(text: str) -> str:
    """Normalize Teledyne model number variants to canonical forms.

    Rules:
    - "Model 465" / "model #465" → "M465"
    - "Model 465H" / "model #465H" → "M465H"
    - "Model 3350" / "model #3350" → "3350"
    - Bare "465H" → "M465H", bare "460" → "M460"
    - Bare "3350" → "3350" (no M prefix for 4-digit)
    - Already-canonical "M465" stays "M465"
    - Idempotent: normalize(normalize(x)) == normalize(x)
    """
    result = text

    # 1. Handle "Model NNN" / "Model #NNN" patterns
    def _replace_model_prefix(m: re.Match) -> str:
        digits, suffix = m.group(1), m.group(2).upper()
        if digits in _THREE_DIGIT_MODELS:
            return f"M{digits}{suffix}"
        if digits in _FOUR_DIGIT_MODELS:
            return f"{digits}{suffix}"
        # Unknown model number — leave with M prefix for 3-digit, bare for 4-digit
        if len(digits) == 3:
            return f"M{digits}{suffix}"
        return f"{digits}{suffix}"

    result = _MODEL_PREFIX_RE.sub(_replace_model_prefix, result)

    # 2. Handle bare 3-digit numbers (460, 465, 480) — prefix with M
    def _replace_bare_three(m: re.Match) -> str:
        digits, suffix = m.group(1), m.group(2).upper()
        if digits not in _THREE_DIGIT_MODELS:
            return m.group(0)  # not a known model, leave alone
        # Check if already preceded by 'M' (already canonical)
        start = m.start()
        if start > 0 and result[start - 1] in ("M", "m"):
            return m.group(0)
        return f"M{digits}{suffix}"

    result = _BARE_THREE_DIGIT_RE.sub(_replace_bare_three, result)

    # 3. Bare 4-digit numbers (3350, 3550) — keep as-is (no M prefix)
    # They are already canonical, nothing to do.

    return result

# ── Query rewriting: error code expansion ───────────────────────────

# Patterns for error codes we want to expand
_ERROR_CODE_EXPAND_RE = re.compile(
    r"\b(E\d{2,4}|ERR-?\d+|F\d{2,4}|Alarm\s+\d+)\b",
    re.IGNORECASE,
)


def expand_error_code(text: str) -> str:
    """Expand error codes with synonym terms for better retrieval.

    "E04" → "E04 error code fault"
    "Alarm 15" → "Alarm 15 alarm code fault"
    "ERR-12" → "ERR-12 error code fault"
    "F03" → "F03 error code fault"

    Preserves original code in output, appends synonym terms.
    If no error codes found, returns text unchanged.
    """
    matches = list(_ERROR_CODE_EXPAND_RE.finditer(text))
    if not matches:
        return text

    # Build result by expanding each error code in-place
    result = text
    offset = 0
    for m in matches:
        code = m.group(0)
        code_upper = code.upper().strip()
        # Determine synonym terms based on code type
        if code_upper.startswith("ALARM"):
            expansion = f"{code} alarm code fault"
        else:
            expansion = f"{code} error code fault"
        start = m.start() + offset
        end = m.end() + offset
        result = result[:start] + expansion + result[end:]
        offset += len(expansion) - len(code)

    return result


# ── Query rewriting: part number sub-query extraction ───────────────

# Refined part number pattern: numeric-heavy identifiers
_PART_NUMBER_SUBQUERY_RE = re.compile(
    r"\b(\d{5,9}[A-Z0-9-]*|[A-Z]{2}\d{5,9})\b",
    re.IGNORECASE,
)


def generate_part_number_subquery(question: str) -> str | None:
    """Extract part numbers and return a lexical-only sub-query.

    Returns a string containing only the part number tokens,
    or None if no part numbers are found.

    Example: "where is part 066560000 used" → "066560000"
    Example: "PL1234567 replacement" → "PL1234567"
    """
    matches = _PART_NUMBER_SUBQUERY_RE.findall(question)
    if not matches:
        return None
    # Return space-joined part number tokens only
    return " ".join(matches)


# ── Query rewriting: multi-entity query splitting ───────────────────

# Matches canonical and variant model numbers in text
_MULTI_MODEL_RE = re.compile(
    r"\b(M\d{3}[A-Za-z]*|model\s*#?\s*\d{3,4}[A-Za-z]*|\d{3}[HhLlMm]|3350|3550)\b",
    re.IGNORECASE,
)


def _canonical_model(token: str) -> str:
    """Convert a model token to its canonical form for dedup."""
    return normalize_model_number(token).strip()


def split_multi_entity_query(question: str) -> list[str]:
    """Split a query with N≥2 model numbers into N sub-queries.

    Each sub-query keeps the full question text but with only one
    model number. Returns original as single-element list when
    0 or 1 model numbers found.

    Example:
        "difference between M460 and M465 ozone output"
        → ["difference between M460 and ozone output",
           "difference between and M465 ozone output"]
    """
    matches = list(_MULTI_MODEL_RE.finditer(question))
    if len(matches) < 2:
        return [question]

    # Deduplicate by canonical form, keeping first occurrence
    seen: dict[str, re.Match] = {}
    unique_matches: list[re.Match] = []
    for m in matches:
        canon = _canonical_model(m.group(0))
        if canon not in seen:
            seen[canon] = m
            unique_matches.append(m)

    if len(unique_matches) < 2:
        return [question]

    sub_queries: list[str] = []
    for keep_match in unique_matches:
        # Remove all OTHER model numbers, keep this one
        parts: list[str] = []
        last_end = 0
        for m in matches:
            if m is keep_match:
                parts.append(question[last_end:m.end()])
            else:
                parts.append(question[last_end:m.start()])
            last_end = m.end()
        parts.append(question[last_end:])
        sub_q = " ".join("".join(parts).split())  # collapse whitespace
        sub_queries.append(sub_q)

    return sub_queries


# ── Query rewriting: equipment context addition ─────────────────────

_TOPIC_KEYWORDS = {
    "troubleshoot", "troubleshooting", "maintenance", "spec",
    "specification", "specifications", "calibration", "calibrate",
    "error", "parts", "procedure", "install", "replace",
    "repair", "setup", "configure", "startup", "safety",
    "warning", "clean", "cleaning", "inspect", "inspection",
}

_EQUIPMENT_CONTEXT = "Teledyne ozone monitor specifications maintenance troubleshooting"

# Detects any known model number in text
_HAS_MODEL_RE = re.compile(
    r"\b(M\d{3}[A-Za-z]*|\d{3}[HhLlMm]|3350|3550|model\s*#?\s*\d{3,4})\b",
    re.IGNORECASE,
)


def add_equipment_context(question: str) -> str:
    """Add context terms when query has a model number but no topic.

    For bare model number queries (e.g. "M465H"), appends
    "Teledyne ozone monitor specifications maintenance troubleshooting".

    If the query already contains topic keywords, returns unchanged.
    """
    if not _HAS_MODEL_RE.search(question):
        return question

    lower = question.lower()
    words = set(re.findall(r"[a-z]+", lower))
    if words & _TOPIC_KEYWORDS:
        return question

    return f"{question} {_EQUIPMENT_CONTEXT}"
