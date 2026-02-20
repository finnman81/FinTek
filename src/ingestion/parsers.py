"""
File-type-specific document parsers.

Extracts raw text + metadata from PDFs, DOCX, TXT, CSV, and Markdown files.
Each parser returns a list of page/section dicts for downstream chunking.
"""

from __future__ import annotations

import csv
import io
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ParsedPage:
    """A single page or section extracted from a document."""
    text: str
    page_number: int | None = None
    section: str = ""
    section_path: str = ""  # e.g. "Ch3 > Maintenance" or "Page 5" for manuals
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedDocument:
    """Full parsed result from a single file."""
    filename: str
    file_type: str
    pages: list[ParsedPage]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def full_text(self) -> str:
        return "\n\n".join(page.text for page in self.pages)

    @property
    def total_pages(self) -> int:
        return len(self.pages)


def parse_pdf(file_path: Path) -> ParsedDocument:
    """Extract text from a PDF file, page by page."""
    import fitz  # PyMuPDF

    doc = fitz.open(str(file_path))
    pages = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        if text.strip():
            pages.append(
                ParsedPage(
                    text=text.strip(),
                    page_number=page_num + 1,
                    section_path=f"Page {page_num + 1}",
                    metadata={"source": file_path.name, "page": page_num + 1},
                )
            )

    total_pages = len(doc)
    doc.close()
    logger.info(f"Parsed PDF '{file_path.name}': {len(pages)} pages with content")

    return ParsedDocument(
        filename=file_path.name,
        file_type="pdf",
        pages=pages,
        metadata={"source_path": str(file_path), "total_pages": total_pages},
    )


def parse_docx(file_path: Path) -> ParsedDocument:
    """Extract text from a DOCX file, paragraph by paragraph."""
    from docx import Document

    doc = Document(str(file_path))
    text_parts = []
    current_section = ""

    for para in doc.paragraphs:
        # Track headings as sections
        if para.style and para.style.name and para.style.name.startswith("Heading"):
            current_section = para.text.strip()

        if para.text.strip():
            text_parts.append((para.text.strip(), current_section))

    # Group into logical sections
    pages = []
    if text_parts:
        current_text_lines = []
        current_sec = text_parts[0][1]

        for text, section in text_parts:
            if section != current_sec and current_text_lines:
                pages.append(
                    ParsedPage(
                        text="\n".join(current_text_lines),
                        section=current_sec,
                        section_path=current_sec or "Document",
                        metadata={"source": file_path.name, "section": current_sec},
                    )
                )
                current_text_lines = []
                current_sec = section
            current_text_lines.append(text)

        if current_text_lines:
            pages.append(
                ParsedPage(
                    text="\n".join(current_text_lines),
                    section=current_sec,
                    section_path=current_sec or "Document",
                    metadata={"source": file_path.name, "section": current_sec},
                )
            )

    logger.info(f"Parsed DOCX '{file_path.name}': {len(pages)} sections")

    return ParsedDocument(
        filename=file_path.name,
        file_type="docx",
        pages=pages,
        metadata={"source_path": str(file_path)},
    )


def parse_txt(file_path: Path) -> ParsedDocument:
    """Extract text from a plain text file."""
    text = file_path.read_text(encoding="utf-8", errors="replace")

    pages = [
        ParsedPage(
            text=text.strip(),
            page_number=1,
            section_path="Document",
            metadata={"source": file_path.name},
        )
    ] if text.strip() else []

    logger.info(f"Parsed TXT '{file_path.name}': {len(text)} characters")

    return ParsedDocument(
        filename=file_path.name,
        file_type="txt",
        pages=pages,
        metadata={"source_path": str(file_path)},
    )


def parse_markdown(file_path: Path) -> ParsedDocument:
    """Extract text from a Markdown file, splitting on headers."""
    text = file_path.read_text(encoding="utf-8", errors="replace")
    lines = text.split("\n")
    pages = []
    current_section = ""
    current_lines: list[str] = []

    for line in lines:
        if line.startswith("#"):
            if current_lines:
                pages.append(
                    ParsedPage(
                        text="\n".join(current_lines).strip(),
                        section=current_section,
                        section_path=current_section or "Document",
                        metadata={"source": file_path.name, "section": current_section},
                    )
                )
                current_lines = []
            current_section = line.lstrip("#").strip()

        current_lines.append(line)

    if current_lines:
        pages.append(
            ParsedPage(
                text="\n".join(current_lines).strip(),
                section=current_section,
                section_path=current_section or "Document",
                metadata={"source": file_path.name, "section": current_section},
            )
        )

    logger.info(f"Parsed Markdown '{file_path.name}': {len(pages)} sections")

    return ParsedDocument(
        filename=file_path.name,
        file_type="markdown",
        pages=pages,
        metadata={"source_path": str(file_path)},
    )


def parse_csv(file_path: Path) -> ParsedDocument:
    """Extract text from a CSV file, converting rows to readable text."""
    text = file_path.read_text(encoding="utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))

    rows_text = []
    for row in reader:
        row_str = " | ".join(f"{k}: {v}" for k, v in row.items() if v)
        if row_str:
            rows_text.append(row_str)

    pages = [
        ParsedPage(
            text="\n".join(rows_text),
            page_number=1,
            section_path="Table",
            metadata={"source": file_path.name, "row_count": len(rows_text)},
        )
    ] if rows_text else []

    logger.info(f"Parsed CSV '{file_path.name}': {len(rows_text)} rows")

    return ParsedDocument(
        filename=file_path.name,
        file_type="csv",
        pages=pages,
        metadata={"source_path": str(file_path), "row_count": len(rows_text)},
    )


PARSER_REGISTRY: dict[str, Any] = {
    ".pdf": parse_pdf,
    ".docx": parse_docx,
    ".txt": parse_txt,
    ".md": parse_markdown,
    ".csv": parse_csv,
}


def parse_document(file_path: Path) -> ParsedDocument:
    """
    Parse a document file based on its extension.

    Args:
        file_path: Path to the document file.

    Returns:
        ParsedDocument with extracted text and metadata.

    Raises:
        ValueError: If the file type is not supported.
    """
    ext = file_path.suffix.lower()
    parser = PARSER_REGISTRY.get(ext)

    if parser is None:
        supported = ", ".join(PARSER_REGISTRY.keys())
        raise ValueError(f"Unsupported file type '{ext}'. Supported: {supported}")

    return parser(file_path)
