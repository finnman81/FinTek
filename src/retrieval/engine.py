"""
RAG Retrieval Engine.

Orchestrates the full query flow: embed → (hybrid or dense) search →
optional rerank → context assembly → LLM response with citations.
"""

from __future__ import annotations

import json
import logging
import os
from difflib import SequenceMatcher
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from src.llm.base import BaseLLMProvider, BaseEmbeddingProvider, LLMResponse
from src.llm.prompts import (
    build_chat_messages,
    build_extract_sentences_messages,
    build_compose_from_extracted_messages,
    citation_bracket,
    NO_CONTEXT_GENERAL_PROMPT,
    NO_CONTEXT_RESPONSE,
)
from src.retrieval.query_rewrite import (
    detect_query_profile,
    extract_query_entities,
    detect_numeric_intent,
    is_safety_chunk,
    is_spec_or_table_chunk,
)
from src.vectorstore.base import BaseVectorStore, SearchResult

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Full result from a retrieval + generation cycle."""
    answer: str
    sources: list[dict[str, Any]]
    model: str = ""
    usage: dict[str, int] = field(default_factory=dict)
    confidence: float = 0.0


class RetrievalEngine:
    """
    Core RAG engine: embed → (hybrid or dense) search → optional rerank → generate.
    """

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        embedding_provider: BaseEmbeddingProvider,
        vector_store: BaseVectorStore,
        top_k: int = 5,
        score_threshold: float = 0.0,
        use_hybrid: bool = False,
        vector_top_k: int = 40,
        lexical_top_k: int = 40,
        rrf_k: int = 60,
        final_k: int = 20,
        ef_search: int = 80,
        use_reranker: bool = False,
        rerank_top_n: int = 20,
        final_context_chunks: int = 10,
        use_two_pass_answer: bool = False,
        abstain_min_top1_score: float = 0.18,
        abstain_min_top1_top3_ratio: float = 1.05,
        reranker: Any = None,
    ):
        self.llm = llm_provider
        self.embedder = embedding_provider
        self.vector_store = vector_store
        self.top_k = top_k
        self.score_threshold = score_threshold
        self.use_hybrid = use_hybrid
        self.vector_top_k = vector_top_k
        self.lexical_top_k = lexical_top_k
        self.rrf_k = rrf_k
        self.final_k = final_k
        self.ef_search = ef_search
        self.use_reranker = use_reranker
        self.rerank_top_n = rerank_top_n
        self.final_context_chunks = final_context_chunks
        self.use_two_pass_answer = use_two_pass_answer
        self.abstain_min_top1_score = abstain_min_top1_score
        self.abstain_min_top1_top3_ratio = abstain_min_top1_top3_ratio
        self.reranker = reranker
        self.debug_trace_enabled = os.getenv("RAG_DEBUG_TRACE", "0") == "1"
        self.debug_trace_path = Path(os.getenv("RAG_DEBUG_TRACE_PATH", "results/rag_debug_trace.jsonl"))

    def query(
        self,
        question: str,
        conversation_history: list[dict[str, str]] | None = None,
        metadata_filter: dict[str, Any] | None = None,
    ) -> RetrievalResult:
        """
        Execute a full RAG query: embed → retrieve → generate.

        Args:
            question: The user's question.
            conversation_history: Prior conversation turns for context.
            metadata_filter: Optional filter to narrow search (e.g., by document).

        Returns:
            RetrievalResult with answer, sources, and metadata.
        """
        logger.info(f"Processing query: {question[:100]}...")
        trace: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": question,
            "use_hybrid": self.use_hybrid,
            "use_reranker": self.use_reranker,
            "use_two_pass_answer": self.use_two_pass_answer,
        }

        # 1. Embed the question
        query_embedding = self.embedder.embed_text(question)

        profile = detect_query_profile(question)
        entity_filter = self._build_metadata_filter(question)

        # 2. Retrieve (hybrid or dense)
        search_results, retrieval_debug = self._retrieve_with_debug(
            question,
            query_embedding,
            metadata_filter or entity_filter,
            profile,
            include_debug=self.debug_trace_enabled,
        )
        if retrieval_debug:
            trace.update(retrieval_debug)
        if self.debug_trace_enabled:
            trace["fused_results_before_rerank"] = [
                {"id": r.document_id, "score": r.score} for r in search_results
            ]

        # 3. Optional rerank then take top N
        if self.use_reranker and self.reranker and search_results:
            passages = [r.text for r in search_results]
            reranked = self.reranker.rerank(question, passages, top_n=self.rerank_top_n)
            by_idx = {i: r for i, r in enumerate(search_results)}
            if self.debug_trace_enabled:
                trace["reranker_ranked_indices"] = [{"idx": i, "score": s} for i, s in reranked]
            search_results = [by_idx[i] for i, _ in reranked if i in by_idx]
        if self.debug_trace_enabled:
            trace["reranked_top_n_chunks"] = [
                {"id": r.document_id, "score": r.score} for r in search_results[: self.rerank_top_n]
            ]
            trace["query_profile"] = profile
            trace["metadata_filter"] = metadata_filter or entity_filter
        keep = self.final_context_chunks if (self.use_hybrid or self.use_reranker) else self.top_k
        search_results = search_results[:keep]

        # 4. No global score threshold (rely on topK + rerank). Optionally filter only if threshold > 0.
        if self.score_threshold > 0:
            relevant_results = [r for r in search_results if r.score >= self.score_threshold]
        else:
            relevant_results = search_results

        if self._should_abstain(relevant_results):
            fallback_messages = [
                {"role": "user", "content": NO_CONTEXT_GENERAL_PROMPT.format(question=question)},
            ]
            fallback_response = self.llm.generate(fallback_messages)
            return RetrievalResult(
                answer=fallback_response.content,
                sources=[],
                model=fallback_response.model,
                usage=fallback_response.usage,
                confidence=0.0,
            )

        if not relevant_results:
            logger.info("No relevant documents found; using no-context response")
            fallback_messages = [
                {"role": "user", "content": NO_CONTEXT_GENERAL_PROMPT.format(question=question)},
            ]
            fallback_response = self.llm.generate(fallback_messages)
            if self.debug_trace_enabled:
                trace["assembled_prompt_messages"] = fallback_messages
                trace["raw_model_output"] = fallback_response.content
                trace["returned_answer"] = fallback_response.content
                self._append_debug_trace(trace)
            return RetrievalResult(
                answer=fallback_response.content,
                sources=[],
                model=fallback_response.model,
                usage=fallback_response.usage,
                confidence=0.0,
            )

        # 5. Manual-aware context assembly (dedupe, prefer procedure/safety/spec)
        assembled = self._assemble_context(relevant_results, question)
        context_chunks = self._format_context(assembled)
        if self.debug_trace_enabled:
            trace["final_context_preview"] = "\n\n".join(c.get("text", "") for c in context_chunks[:2])

        # 6. Generate response (two-pass or single-pass)
        if self.use_two_pass_answer and context_chunks:
            # Pass 1: extract 3–5 relevant sentences with citations
            extract_messages = build_extract_sentences_messages(question, context_chunks)
            extract_response = self.llm.generate(extract_messages)
            extracted_text = extract_response.content.strip()
            # Pass 2: compose final answer strictly from extracted text
            compose_messages = build_compose_from_extracted_messages(question, extracted_text)
            compose_response = self.llm.generate(compose_messages)
            # Merge token usage from both passes
            u1 = extract_response.usage or {}
            u2 = compose_response.usage or {}
            merged_usage = {
                "prompt_tokens": u1.get("prompt_tokens", 0) + u2.get("prompt_tokens", 0),
                "completion_tokens": u1.get("completion_tokens", 0) + u2.get("completion_tokens", 0),
                "total_tokens": u1.get("total_tokens", 0) + u2.get("total_tokens", 0),
            }
            llm_response = LLMResponse(
                content=compose_response.content,
                model=compose_response.model,
                usage=merged_usage,
                metadata=compose_response.metadata,
            )
            logger.info("Two-pass answer: extract + compose")
            if self.debug_trace_enabled:
                trace["assembled_prompt_messages"] = {
                    "extract_messages": extract_messages,
                    "compose_messages": compose_messages,
                }
                trace["raw_model_output"] = compose_response.content
        else:
            messages = build_chat_messages(
                user_question=question,
                context_chunks=context_chunks,
                conversation_history=conversation_history,
            )
            llm_response = self.llm.generate(messages)
            if self.debug_trace_enabled:
                trace["assembled_prompt_messages"] = messages
                trace["raw_model_output"] = llm_response.content

        llm_response.content = self._repair_missing_citations(llm_response.content, relevant_results)

        # 7. Extract unique sources
        sources = self._extract_sources(relevant_results)

        avg_score = sum(r.score for r in relevant_results) / len(relevant_results)

        logger.info(
            f"Query complete: {len(relevant_results)} sources, "
            f"avg_score={avg_score:.3f}, tokens={llm_response.usage.get('total_tokens', 0)}"
        )
        if self.debug_trace_enabled:
            trace["returned_answer"] = llm_response.content
            trace["sources"] = sources
            self._append_debug_trace(trace)

        return RetrievalResult(
            answer=llm_response.content,
            sources=sources,
            model=llm_response.model,
            usage=llm_response.usage,
            confidence=avg_score,
        )

    def _append_debug_trace(self, payload: dict[str, Any]) -> None:
        """Append one query trace record to JSONL when RAG_DEBUG_TRACE=1."""
        try:
            self.debug_trace_path.parent.mkdir(parents=True, exist_ok=True)
            with self.debug_trace_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=True) + "\n")
        except Exception as e:
            logger.warning(f"Failed to write RAG debug trace: {e}")

    def query_stream(
        self,
        question: str,
        conversation_history: list[dict[str, str]] | None = None,
        metadata_filter: dict[str, Any] | None = None,
    ) -> tuple[Iterator[str], list[dict[str, Any]]]:
        """
        Execute a RAG query with streaming LLM response.

        Returns:
            Tuple of (token stream iterator, sources list).
        """
        query_embedding = self.embedder.embed_text(question)
        search_results = self._retrieve(question, query_embedding, metadata_filter)
        if self.use_reranker and self.reranker and search_results:
            passages = [r.text for r in search_results]
            reranked = self.reranker.rerank(question, passages, top_n=self.rerank_top_n)
            by_idx = {i: r for i, r in enumerate(search_results)}
            search_results = [by_idx[i] for i, _ in reranked if i in by_idx]
        keep = self.final_context_chunks if (self.use_hybrid or self.use_reranker) else self.top_k
        search_results = search_results[:keep]
        if self.score_threshold > 0:
            relevant_results = [r for r in search_results if r.score >= self.score_threshold]
        else:
            relevant_results = search_results

        if not relevant_results:
            def empty_stream() -> Iterator[str]:
                yield NO_CONTEXT_RESPONSE
            return empty_stream(), []

        assembled = self._assemble_context(relevant_results, question)
        context_chunks = self._format_context(assembled)
        messages = build_chat_messages(
            user_question=question,
            context_chunks=context_chunks,
            conversation_history=conversation_history,
        )

        # 4. Stream response
        token_stream = self.llm.stream(messages)
        sources = self._extract_sources(relevant_results)

        return token_stream, sources

    def _retrieve(
        self,
        question: str,
        query_embedding: list[float],
        metadata_filter: dict[str, Any] | None,
        profile: str = "general",
    ) -> list[SearchResult]:
        """Run hybrid or dense-only retrieval."""
        params = self._profile_params(profile)
        if self.use_hybrid and hasattr(self.vector_store, "search_hybrid"):
            return self.vector_store.search_hybrid(
                query_text=question,
                query_embedding=query_embedding,
                vector_top_k=params["vector_top_k"],
                lexical_top_k=params["lexical_top_k"],
                rrf_k=self.rrf_k,
                final_k=params["final_k"],
                ef_search=self.ef_search,
                metadata_filter=metadata_filter,
            )
        return self.vector_store.search(
            query_embedding=query_embedding,
            top_k=params["top_k"],
            metadata_filter=metadata_filter,
        )

    def _retrieve_with_debug(
        self,
        question: str,
        query_embedding: list[float],
        metadata_filter: dict[str, Any] | None,
        profile: str = "general",
        include_debug: bool = False,
    ) -> tuple[list[SearchResult], dict[str, Any]]:
        """Retrieve results and, when available, retrieval stage debug details."""
        debug: dict[str, Any] = {}
        params = self._profile_params(profile)
        if self.use_hybrid and hasattr(self.vector_store, "search_hybrid_with_debug"):
            results, hybrid_debug = self.vector_store.search_hybrid_with_debug(
                query_text=question,
                query_embedding=query_embedding,
                vector_top_k=params["vector_top_k"],
                lexical_top_k=params["lexical_top_k"],
                rrf_k=self.rrf_k,
                final_k=params["final_k"],
                ef_search=self.ef_search,
                metadata_filter=metadata_filter,
                include_debug=include_debug,
            )
            return results, hybrid_debug or {}

        results = self._retrieve(question, query_embedding, metadata_filter, profile=profile)
        if include_debug and not self.use_hybrid:
            debug["vector_hits"] = [{"id": r.document_id, "score": r.score} for r in results]
        return results, debug

    def _similarity(self, a: str, b: str) -> float:
        """Ratio of similarity between two strings (0-1)."""
        return SequenceMatcher(None, a.strip().lower(), b.strip().lower()).ratio()

    def _dedupe_by_similarity(
        self, results: list[SearchResult], similarity_threshold: float = 0.90
    ) -> list[SearchResult]:
        """Keep higher-scoring chunk when two are very similar (e.g. 90% same)."""
        if len(results) <= 1:
            return results
        kept: list[SearchResult] = []
        for r in results:
            is_dupe = False
            for k in kept:
                if self._similarity(r.text, k.text) >= similarity_threshold:
                    is_dupe = True
                    break
            if not is_dupe:
                kept.append(r)
        return kept

    def _assemble_context(
        self, results: list[SearchResult], question: str
    ) -> list[SearchResult]:
        """Deduplicate (prefix + similarity) and reorder: procedure first, then safety, then spec if numeric."""
        if not results:
            return results
        # 1. Dedupe by normalized text prefix
        seen_prefix: set[str] = set()
        by_prefix: list[SearchResult] = []
        for r in results:
            prefix = (r.text[:120] + "..").strip().lower()
            if prefix in seen_prefix:
                continue
            seen_prefix.add(prefix)
            by_prefix.append(r)
        # 2. Dedupe by high similarity (keep higher score)
        deduped = self._dedupe_by_similarity(by_prefix, similarity_threshold=0.90)
        # 3. Order: procedure first, then one safety, then one spec if numeric, then rest
        procedure: list[SearchResult] = []
        safety: list[SearchResult] = []
        spec: list[SearchResult] = []
        other: list[SearchResult] = []
        for r in deduped:
            if is_safety_chunk(r.metadata):
                safety.append(r)
            elif is_spec_or_table_chunk(r.metadata):
                spec.append(r)
            elif (r.metadata.get("content_type") or "").lower() == "procedure":
                procedure.append(r)
            else:
                other.append(r)
        numeric = detect_numeric_intent(question)
        out: list[SearchResult] = procedure[:2]
        if safety:
            out.append(safety[0])
        if numeric and spec:
            out.append(spec[0])
        rest = [r for r in deduped if r not in out]
        out.extend(rest)
        return out[: self.final_context_chunks if (self.use_hybrid or self.use_reranker) else self.top_k]

    def _build_metadata_filter(self, question: str) -> dict[str, Any] | None:
        entities = extract_query_entities(question)
        filt: dict[str, Any] = {}
        if entities.get("error_codes"):
            filt["error_codes"] = entities["error_codes"]
        if entities.get("part_numbers"):
            filt["part_numbers"] = entities["part_numbers"]
        return filt or None

    def _profile_params(self, profile: str) -> dict[str, int]:
        params = {
            "top_k": self.top_k,
            "vector_top_k": self.vector_top_k,
            "lexical_top_k": self.lexical_top_k,
            "final_k": self.final_k,
        }
        if profile in {"error_codes", "spec_lookup"}:
            params["vector_top_k"] = max(20, self.vector_top_k - 10)
            params["lexical_top_k"] = self.lexical_top_k + 10
            params["final_k"] = max(8, self.final_k - 4)
            params["top_k"] = max(5, self.top_k - 1)
        elif profile in {"procedures", "troubleshooting"}:
            params["vector_top_k"] = self.vector_top_k + 10
            params["final_k"] = self.final_k
        return params

    def _should_abstain(self, results: list[SearchResult]) -> bool:
        if not results:
            return True
        top1 = results[0].score
        if len(results) >= 3:
            ratio = top1 / max(results[2].score, 1e-6)
        else:
            ratio = 1.0
        return top1 < self.abstain_min_top1_score and ratio < self.abstain_min_top1_top3_ratio

    def _repair_missing_citations(self, answer: str, results: list[SearchResult]) -> str:
        if not answer or "[" in answer or not results:
            return answer
        top_citation = citation_bracket(results[0].metadata)
        lines = [ln.strip() for ln in answer.split("\n") if ln.strip()]
        repaired = [ln if ln.endswith("]") else f"{ln} {top_citation}" for ln in lines]
        return "\n".join(repaired)

    def _format_context(self, results: list[SearchResult]) -> list[dict]:
        """Format search results into context chunks for the prompt."""
        return [
            {
                "text": f"{citation_bracket(r.metadata)}\n{r.text}",
                "metadata": r.metadata,
                "score": r.score,
            }
            for r in results
        ]

    def _extract_sources(self, results: list[SearchResult]) -> list[dict[str, Any]]:
        """Extract unique source documents from search results."""
        seen = set()
        sources = []

        for r in results:
            source_name = r.metadata.get("source", "Unknown")
            page = r.metadata.get("page", "") or r.metadata.get("page_start", "")
            section = r.metadata.get("section", "") or r.metadata.get("section_path", "")
            key = f"{source_name}:{page}:{section}"

            if key not in seen:
                seen.add(key)
                sources.append({
                    "source": source_name,
                    "document": source_name,
                    "page": page,
                    "section": section,
                    "text": r.text,
                    "relevance_score": round(r.score, 3),
                })

        return sources
