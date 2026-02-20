"""
Unit tests for RetrievalEngine with mocked LLM and vector store.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.retrieval.engine import RetrievalEngine
from src.llm.base import LLMResponse
from src.vectorstore.base import BaseVectorStore, SearchResult


def _make_mock_embedder(dim: int = 1536):
    embedder = MagicMock()
    embedder.embed_text.return_value = [0.1] * dim
    embedder.embed_batch.return_value = [[0.1] * dim]
    embedder.dimensions = dim
    return embedder


def _make_mock_llm():
    llm = MagicMock()
    llm.generate.return_value = LLMResponse(
        content="The pump must be primed before start.",
        model="gpt-4o",
        usage={"total_tokens": 80, "prompt_tokens": 40, "completion_tokens": 40},
    )
    def stream_fn(*args, **kwargs):
        for word in ["The ", "pump ", "must ", "be ", "primed."]:
            yield word
    llm.stream.side_effect = stream_fn
    return llm


def _make_mock_vector_store(results: list[SearchResult] | None = None):
    if results is None:
        results = [
            SearchResult(
                text="Priming procedure: open valve A, then B.",
                score=0.88,
                metadata={"source": "manual.pdf", "page": 5},
                document_id="c1",
            ),
        ]
    store = MagicMock(spec=BaseVectorStore)
    store.search.return_value = results
    return store


class TestRetrievalEngineQuery:
    def test_query_returns_retrieval_result(self):
        engine = RetrievalEngine(
            llm_provider=_make_mock_llm(),
            embedding_provider=_make_mock_embedder(),
            vector_store=_make_mock_vector_store(),
            top_k=5,
            score_threshold=0.3,
        )
        result = engine.query("How do I prime the pump?")
        assert result.answer
        assert "primed" in result.answer.lower() or "pump" in result.answer.lower()
        assert result.confidence >= 0.3
        assert len(result.sources) >= 1
        assert result.model == "gpt-4o"
        assert result.usage.get("total_tokens", 0) >= 0

    def test_query_no_relevant_results_below_threshold_returns_no_context_message(self):
        store = _make_mock_vector_store([
            SearchResult(text="Irrelevant.", score=0.1, metadata={}, document_id="x"),
        ])
        engine = RetrievalEngine(
            llm_provider=_make_mock_llm(),
            embedding_provider=_make_mock_embedder(),
            vector_store=store,
            top_k=5,
            score_threshold=0.5,
        )
        result = engine.query("Specific question?")
        assert result.answer
        assert result.sources == []
        assert result.confidence == 0.0
        # Fallback response is generated through LLM prompt.
        engine.llm.generate.assert_called()

    def test_query_calls_embedder_and_vector_store(self):
        embedder = _make_mock_embedder()
        store = _make_mock_vector_store()
        llm = _make_mock_llm()
        engine = RetrievalEngine(
            llm_provider=llm,
            embedding_provider=embedder,
            vector_store=store,
            top_k=3,
            score_threshold=0.3,
        )
        engine.query("Test question?")
        embedder.embed_text.assert_called_once_with("Test question?")
        store.search.assert_called_once()
        llm.generate.assert_called_once()




    def test_query_repairs_missing_citations(self):
        store = _make_mock_vector_store([
            SearchResult(text="Pump priming requires opening valve A.", score=0.9, metadata={"source": "manual.pdf", "page": 3}, document_id="x1"),
        ])
        llm = _make_mock_llm()
        llm.generate.return_value = LLMResponse(
            content="Open valve A first.",
            model="gpt-4o",
            usage={"total_tokens": 10, "prompt_tokens": 5, "completion_tokens": 5},
        )
        engine = RetrievalEngine(
            llm_provider=llm,
            embedding_provider=_make_mock_embedder(),
            vector_store=store,
            score_threshold=0.0,
        )
        result = engine.query("How to prime?")
        assert "[manual.pdf|p=3]" in result.answer

    def test_query_uses_metadata_filter_for_error_codes(self):
        store = _make_mock_vector_store()
        engine = RetrievalEngine(
            llm_provider=_make_mock_llm(),
            embedding_provider=_make_mock_embedder(),
            vector_store=store,
            use_hybrid=False,
        )
        engine.query("What does error code E10 mean?")
        kwargs = store.search.call_args.kwargs
        assert kwargs.get("metadata_filter") is not None
        assert "E10" in kwargs["metadata_filter"].get("error_codes", [])


class TestRetrievalEngineQueryStream:
    def test_query_stream_returns_iterator_and_sources(self):
        engine = RetrievalEngine(
            llm_provider=_make_mock_llm(),
            embedding_provider=_make_mock_embedder(),
            vector_store=_make_mock_vector_store(),
            top_k=5,
            score_threshold=0.3,
        )
        token_stream, sources = engine.query_stream("How to prime?")
        tokens = list(token_stream)
        assert len(tokens) >= 1
        assert "".join(tokens)
        assert isinstance(sources, list)

    def test_query_stream_no_results_returns_no_context_message(self):
        store = _make_mock_vector_store([SearchResult("x", 0.1, {}, "")])
        engine = RetrievalEngine(
            llm_provider=_make_mock_llm(),
            embedding_provider=_make_mock_embedder(),
            vector_store=store,
            score_threshold=0.5,
        )
        stream, sources = engine.query_stream("Question?")
        text = "".join(stream)
        assert "not found" in text.lower()
        assert sources == []
