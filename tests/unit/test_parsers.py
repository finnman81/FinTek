"""
Unit tests for document parsers (TXT, CSV, Markdown). PDF/DOCX require binary files.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.ingestion.parsers import (
    parse_txt,
    parse_csv,
    parse_markdown,
    parse_document,
    ParsedDocument,
    ParsedPage,
    PARSER_REGISTRY,
)


class TestParsedDocument:
    def test_full_text_and_total_pages(self):
        doc = ParsedDocument(
            filename="a.txt",
            file_type="txt",
            pages=[
                ParsedPage(text="Page 1", page_number=1),
                ParsedPage(text="Page 2", page_number=2),
            ],
        )
        assert doc.total_pages == 2
        assert "Page 1" in doc.full_text and "Page 2" in doc.full_text


class TestParseTxt:
    def test_simple_txt(self, tmp_path: Path):
        f = tmp_path / "doc.txt"
        f.write_text("Hello world.\nSecond line.")
        doc = parse_txt(f)
        assert doc.filename == "doc.txt"
        assert doc.file_type == "txt"
        assert len(doc.pages) == 1
        assert "Hello world" in doc.pages[0].text

    def test_empty_txt_returns_empty_pages(self, tmp_path: Path):
        f = tmp_path / "empty.txt"
        f.write_text("   \n\t  ")
        doc = parse_txt(f)
        assert doc.pages == []


class TestParseCsv:
    def test_simple_csv(self, tmp_path: Path):
        f = tmp_path / "data.csv"
        f.write_text("name,value\nalice,1\nbob,2")
        doc = parse_csv(f)
        assert doc.filename == "data.csv"
        assert doc.file_type == "csv"
        assert len(doc.pages) == 1
        assert "alice" in doc.pages[0].text and "bob" in doc.pages[0].text

    def test_empty_csv_returns_empty_pages(self, tmp_path: Path):
        f = tmp_path / "empty.csv"
        f.write_text("a,b\n")
        doc = parse_csv(f)
        assert doc.pages == []


class TestParseMarkdown:
    def test_markdown_with_headers(self, tmp_path: Path):
        f = tmp_path / "readme.md"
        f.write_text("# Title\n\nIntro.\n\n## Section 1\n\nContent one.\n\n## Section 2\n\nContent two.")
        doc = parse_markdown(f)
        assert doc.file_type == "markdown"
        assert len(doc.pages) >= 1
        assert any("Content one" in p.text for p in doc.pages)


class TestParseDocument:
    def test_txt_dispatches_to_parse_txt(self, tmp_path: Path):
        f = tmp_path / "x.txt"
        f.write_text("Hello")
        doc = parse_document(f)
        assert doc.file_type == "txt"
        assert len(doc.pages) == 1

    def test_csv_dispatches_to_parse_csv(self, tmp_path: Path):
        f = tmp_path / "x.csv"
        f.write_text("a,b\n1,2")
        doc = parse_document(f)
        assert doc.file_type == "csv"

    def test_md_dispatches_to_parse_markdown(self, tmp_path: Path):
        f = tmp_path / "x.md"
        f.write_text("# Hi\n\nBody.")
        doc = parse_document(f)
        assert doc.file_type == "markdown"

    def test_unsupported_extension_raises(self, tmp_path: Path):
        f = tmp_path / "x.xyz"
        f.write_text("data")
        with pytest.raises(ValueError, match="Unsupported file type"):
            parse_document(f)

    def test_parser_registry_has_expected_extensions(self):
        assert ".txt" in PARSER_REGISTRY
        assert ".csv" in PARSER_REGISTRY
        assert ".md" in PARSER_REGISTRY
        assert ".pdf" in PARSER_REGISTRY
        assert ".docx" in PARSER_REGISTRY
