"""
Text chunking strategies for document processing.

Splits by words (not characters) for manuals; preserves procedures and tables.
Parent = full section; children = 150-300 words with 25-60 word overlap.
Separators: paragraph, newline, sentence, space (no comma to avoid shredding specs/tables).
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# Manual-friendly extraction patterns
PART_NUMBER_PATTERN = re.compile(
    r"\b(?:\d{4,8}[-\s]?[A-Z0-9]+|[A-Z]{2,4}\s?\d{4,8})\b",
    re.IGNORECASE,
)
ERROR_CODE_PATTERN = re.compile(
    r"\b(?:E\d{2,4}|ERR[- ]?\d+|Fault\s*#?\s*\d+)\b",
    re.IGNORECASE,
)
MODEL_PATTERN = re.compile(
    r"\b(?:Model\s*#?\s*[\w.-]+|Model\s*:?\s*[\w.-]+)\b",
    re.IGNORECASE,
)

# No comma in separators — avoids shredding spec sentences and tables
WORD_SPLIT_SEPARATORS = ["\n\n", "\n", ". ", " "]


def _word_count(text: str) -> int:
    """Count words (whitespace-split)."""
    return len(text.split()) if text.strip() else 0


def extract_manual_metadata(text: str) -> dict[str, Any]:
    """Extract part numbers, error codes, and model number from chunk text."""
    part_numbers = list({m.strip() for m in PART_NUMBER_PATTERN.findall(text)})
    error_codes = list({m.strip() for m in ERROR_CODE_PATTERN.findall(text)})
    model_match = MODEL_PATTERN.search(text)
    model_number = model_match.group(0).strip() if model_match else None
    return {
        "part_numbers": part_numbers[:20],
        "error_codes": error_codes[:20],
        "model_number": model_number,
    }


@dataclass
class Chunk:
    """A single text chunk ready for embedding."""
    text: str
    chunk_index: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SectionGroup:
    """One parent (section) and its child chunks for manual-friendly retrieval."""
    section_path: str
    page_start: int | None
    page_end: int | None
    content_type: str
    parent_text: str
    child_texts: list[str]
    base_metadata: dict[str, Any]


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    metadata: dict[str, Any] | None = None,
) -> list[Chunk]:
    """
    Split text into overlapping chunks (character-based, for non-manual fallback).
    Uses separators without comma to preserve spec/table meaning.
    """
    if not text.strip():
        return []

    base_metadata = metadata or {}
    separators = ["\n\n", "\n", ". ", " ", ""]
    raw_chunks = _recursive_split(text, separators, chunk_size)
    chunks_with_overlap = _apply_overlap(raw_chunks, chunk_overlap)

    chunks = []
    for i, chunk_text_str in enumerate(chunks_with_overlap):
        chunk_meta = {
            **base_metadata,
            "chunk_index": i,
            "chunk_total": len(chunks_with_overlap),
        }
        chunks.append(Chunk(text=chunk_text_str, chunk_index=i, metadata=chunk_meta))

    logger.debug(f"Created {len(chunks)} chunks (size={chunk_size}, overlap={chunk_overlap})")
    return chunks


def _recursive_split(text: str, separators: list[str], chunk_size: int) -> list[str]:
    """Recursively split by character length using best separator (no comma)."""
    if len(text) <= chunk_size:
        return [text.strip()] if text.strip() else []

    for sep in separators:
        if sep and sep in text:
            parts = text.split(sep)
            result = []
            current = ""

            for part in parts:
                candidate = current + sep + part if current else part
                if len(candidate) <= chunk_size:
                    current = candidate
                else:
                    if current:
                        result.append(current.strip())
                    if len(part) > chunk_size:
                        remaining_seps = separators[separators.index(sep) + 1:]
                        result.extend(_recursive_split(part, remaining_seps, chunk_size))
                        current = ""
                    else:
                        current = part

            if current:
                result.append(current.strip())

            return [r for r in result if r]

    return [text[i:i + chunk_size].strip() for i in range(0, len(text), chunk_size) if text[i:i + chunk_size].strip()]


def _apply_overlap(chunks: list[str], overlap: int) -> list[str]:
    """Add overlap from end of previous chunk to start of next."""
    if overlap <= 0 or len(chunks) <= 1:
        return chunks

    result = [chunks[0]]
    for i in range(1, len(chunks)):
        prev = chunks[i - 1]
        overlap_text = prev[-overlap:] if len(prev) > overlap else prev
        result.append(overlap_text + " " + chunks[i])

    return result


def _recursive_split_by_words(
    text: str,
    separators: list[str],
    max_words: int,
) -> list[str]:
    """Split text into chunks of at most max_words, breaking on separators (no comma)."""
    wc = _word_count(text)
    if wc <= max_words:
        return [text.strip()] if text.strip() else []

    for sep in separators:
        if sep and sep in text:
            parts = text.split(sep)
            result = []
            current = ""

            for part in parts:
                candidate = (current + sep + part).strip() if current else part.strip()
                c_words = _word_count(candidate)
                if c_words <= max_words:
                    current = candidate
                else:
                    if current:
                        result.append(current)
                    if _word_count(part) > max_words:
                        remaining = separators[separators.index(sep) + 1:]
                        result.extend(_recursive_split_by_words(part, remaining, max_words))
                        current = ""
                    else:
                        current = part.strip()

            if current:
                result.append(current)

            return [r for r in result if r]

    # Fallback: split by word count
    words = text.split()
    out = []
    for i in range(0, len(words), max_words):
        out.append(" ".join(words[i : i + max_words]))
    return out


def _apply_overlap_words(chunks: list[str], overlap_words: int) -> list[str]:
    """Overlap by word count."""
    if overlap_words <= 0 or len(chunks) <= 1:
        return chunks

    result = [chunks[0]]
    for i in range(1, len(chunks)):
        prev_words = chunks[i - 1].split()
        overlap_tokens = prev_words[-overlap_words:] if len(prev_words) > overlap_words else prev_words
        result.append(" ".join(overlap_tokens) + " " + chunks[i])

    return result


def _infer_content_type(section_path: str) -> str:
    """Infer content_type from section path for manual chunks."""
    lower = section_path.lower()
    if "warning" in lower or "safety" in lower or "caution" in lower:
        return "warning"
    if "spec" in lower or "table" in lower or "specification" in lower:
        return "spec"
    if "table" in lower:
        return "table"
    return "procedure"


def _cap_at_sentence_or_step_boundary(text: str, max_words: int) -> str:
    """Cap text at max_words, breaking at end of sentence or step (numbered list)."""
    words = text.split()
    if len(words) <= max_words:
        return text
    # Take first max_words, then rewind to last sentence or step end
    segment = " ".join(words[: max_words + 1])
    # Prefer break at . \n or ) or numbered step
    for sep in [". ", "\n", "). ", ".\n"]:
        last = segment.rfind(sep)
        if last > max_words * 3:  # at least ~3 chars per word
            return segment[: last + len(sep)].strip()
    return " ".join(words[:max_words])


def chunk_document_parent_child(
    pages: list[Any],
    source_name: str,
    file_type: str,
    child_size: int = 250,
    child_overlap: int = 50,
    parent_max_words: int = 2000,
    *,
    use_words: bool = True,
) -> list[SectionGroup]:
    """
    Chunk by section: one parent per section (full section, not page-cap).
    Children: 150-300 words (child_size) with 25-60 word overlap.
    Parent = full section text, optionally capped by parent_max_words at sentence/step boundary.
    """
    groups: list[SectionGroup] = []

    for page in pages:
        section_path = getattr(page, "section_path", None) or getattr(page, "section", None) or "Document"
        page_start = getattr(page, "page_number", None) or (getattr(page, "metadata", {}) or {}).get("page")
        page_end = page_start
        text = (getattr(page, "text", None) or "").strip()

        if not text:
            continue

        base_metadata = dict(getattr(page, "metadata", {}) or {})
        base_metadata.setdefault("source", source_name)
        base_metadata.setdefault("file_type", file_type)
        base_metadata["section_path"] = section_path
        if page_start is not None:
            base_metadata["page"] = page_start
            base_metadata["page_start"] = page_start

        content_type = _infer_content_type(section_path)

        # Parent = full section (cap by words at sentence/step boundary if needed)
        if use_words and _word_count(text) > parent_max_words:
            parent_text = _cap_at_sentence_or_step_boundary(text, parent_max_words)
        else:
            parent_text = text

        # Children: word-based split (no comma in separators)
        if use_words:
            raw_children = _recursive_split_by_words(text, WORD_SPLIT_SEPARATORS, child_size)
            child_texts = _apply_overlap_words(raw_children, child_overlap) if raw_children else []
        else:
            # Fallback char-based
            raw_children = _recursive_split(text, ["\n\n", "\n", ". ", " ", ""], child_size)
            child_texts = _apply_overlap(raw_children, child_overlap) if raw_children else []

        if not child_texts:
            child_texts = [text[: 500]] if text else []

        groups.append(
            SectionGroup(
                section_path=section_path,
                page_start=page_start,
                page_end=page_end,
                content_type=content_type,
                parent_text=parent_text,
                child_texts=child_texts,
                base_metadata=base_metadata,
            )
        )

    logger.debug(f"Parent-child chunking: {len(groups)} section groups (word-based={use_words})")
    return groups
