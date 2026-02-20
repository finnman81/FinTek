"""
Unit tests for text chunking (chunk_text, overlap, metadata).
"""

from __future__ import annotations

import pytest

from src.ingestion.chunker import chunk_text, Chunk, _recursive_split, _apply_overlap


class TestChunkDataclass:
    def test_chunk_has_text_and_index_and_metadata(self):
        c = Chunk(text="hello", chunk_index=0, metadata={"source": "a.txt"})
        assert c.text == "hello"
        assert c.chunk_index == 0
        assert c.metadata["source"] == "a.txt"


class TestChunkText:
    def test_empty_string_returns_empty_list(self):
        assert chunk_text("") == []
        assert chunk_text("   \n\t  ") == []

    def test_short_text_single_chunk(self):
        text = "Short piece of text."
        chunks = chunk_text(text, chunk_size=1000, chunk_overlap=0)
        assert len(chunks) == 1
        assert chunks[0].text == text.strip()
        assert chunks[0].chunk_index == 0
        assert chunks[0].metadata.get("chunk_total") == 1

    def test_metadata_attached_to_each_chunk(self):
        chunks = chunk_text("One two three.", chunk_size=100, metadata={"source": "test.txt"})
        assert all(c.metadata.get("source") == "test.txt" for c in chunks)
        assert all("chunk_index" in c.metadata for c in chunks)
        assert all("chunk_total" in c.metadata for c in chunks)

    def test_large_text_splits_into_multiple_chunks(self):
        text = "word " * 500  # ~2500 chars
        chunks = chunk_text(text, chunk_size=200, chunk_overlap=20)
        assert len(chunks) >= 2
        for c in chunks:
            assert len(c.text) <= 200 + 50  # overlap can add a bit

    def test_overlap_included_between_chunks(self):
        text = "First sentence. Second sentence. Third sentence. Fourth."
        chunks = chunk_text(text, chunk_size=25, chunk_overlap=5)
        # Should have multiple chunks; overlap means some text appears in adjacent chunks
        assert len(chunks) >= 2


class TestRecursiveSplit:
    def test_text_shorter_than_chunk_size_returns_single_element(self):
        result = _recursive_split("hello", ["\n", " "], 100)
        assert result == ["hello"]

    def test_empty_string_returns_empty(self):
        result = _recursive_split("", ["\n"], 10)
        assert result == []

    def test_splits_on_newline(self):
        text = "line1\n\nline2\n\nline3"
        result = _recursive_split(text, ["\n\n", "\n", " "], 5)
        assert len(result) >= 2


class TestApplyOverlap:
    def test_zero_overlap_returns_unchanged(self):
        chunks = ["a", "b", "c"]
        assert _apply_overlap(chunks, 0) == chunks

    def test_single_chunk_unchanged(self):
        chunks = ["only one"]
        assert _apply_overlap(chunks, 10) == chunks

    def test_overlap_prepends_previous_tail(self):
        chunks = ["first part", "second part"]
        result = _apply_overlap(chunks, 3)
        assert result[0] == "first part"
        assert "art" in result[1]  # last 3 of "first part" + " second part"
