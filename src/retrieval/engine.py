"""
RAG Retrieval Engine.

Thin facade that orchestrates the full query flow: embed → (hybrid or dense)
search → optional rerank → context assembly → LLM response with citations.

Implementation details are delegated to focused modules:
- vector_retrieval: hybrid/dense search, metadata filtering, query text construction
- abstention: score-based abstention decisions and salvage logic
- citations: citation repair for LLM answers
- context: deduplication, reordering, formatting, source extraction
- debug: JSONL trace logging
"""

from __future__ import annotations

import os
import re
import structlog
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from src.llm.base import BaseLLMProvider, BaseEmbeddingProvider, LLMResponse
from src.llm.prompts import (
    build_chat_messages,
    build_extract_sentences_messages,
    build_compose_from_extracted_messages,
    NO_CONTEXT_GENERAL_PROMPT,
    NO_CONTEXT_RESPONSE,
)
from src.retrieval.abstention import (
    should_abstain,
    is_abstention_answer,
    salvage_answer_with_extraction,
    llm_relevance_gate,
)
from src.retrieval.baseline import normalize_query as baseline_normalize_query
from src.retrieval.baseline import run_baseline_retrieval
from src.retrieval.citations import repair_missing_citations
from src.retrieval.context import (
    assemble_context,
    format_context,
    extract_sources,
)
from src.retrieval.debug import append_debug_trace
from src.retrieval.vector_retrieval import (
    build_metadata_filter,
    build_retrieval_query_text,
    boost_content_type,
    boost_model_number_query,
    profile_params,
    retrieve,
    retrieve_with_debug,
)
from src.retrieval.query_rewrite import (
    detect_query_profile,
    generate_lexical_alt,
    normalize_model_number,
    expand_error_code,
)
from src.vectorstore.base import BaseVectorStore, SearchResult

logger = structlog.get_logger()

_CITATION_PATTERN = re.compile(r"\[[^\]|]+\|(?:p=[^\]|]+|s=[^\]]+)(?:\|s=[^\]]+)?\]")


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
        abstain_min_margin: float = 0.05,
        reranker: Any = None,
        use_baseline_path: bool = True,
        baseline_top_k: int = 5,
        content_type_boost: float = 1.3,
        model_number_boost: float = 1.3,
        use_single_pass_fast: bool = False,
        abstention_mode: str = "both",
        use_llm_gate_on_abstain: bool = False,
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
        self.abstain_min_margin = abstain_min_margin
        self.reranker = reranker
        self.use_baseline_path = use_baseline_path
        self.baseline_top_k = baseline_top_k
        self.content_type_boost = content_type_boost
        self.model_number_boost = model_number_boost
        self.use_single_pass_fast = use_single_pass_fast
        self.abstention_mode = abstention_mode
        self.use_llm_gate_on_abstain = use_llm_gate_on_abstain
        self._force_baseline = os.getenv("RAG_FORCE_BASELINE", "").strip() == "1"
        self.debug_trace_enabled = os.getenv("RAG_DEBUG_TRACE", "0") == "1"
        self.debug_trace_path = Path(os.getenv("RAG_DEBUG_TRACE_PATH", "results/rag_debug_trace.jsonl"))

    # ── Helpers that delegate to extracted modules ──────────────────────

    def _keep_count(self) -> int:
        """Number of chunks to keep after reranking/retrieval."""
        return self.final_context_chunks if (self.use_hybrid or self.use_reranker) else self.top_k

    def _use_baseline(self) -> bool:
        """True if the baseline path should be used (config or RAG_FORCE_BASELINE=1)."""
        return self._force_baseline or self.use_baseline_path

    def _build_metadata_filter(self, question: str) -> dict[str, Any] | None:
        return build_metadata_filter(question)

    def _profile_params(self, profile: str) -> dict[str, int]:
        return profile_params(
            profile,
            top_k=self.top_k,
            vector_top_k=self.vector_top_k,
            lexical_top_k=self.lexical_top_k,
            final_k=self.final_k,
        )

    def _build_retrieval_query_text(
        self,
        question: str,
        entity_filter: dict[str, Any] | None,
        profile: str,
    ) -> str:
        return build_retrieval_query_text(question, entity_filter, profile)

    def _should_abstain(self, results: list[SearchResult]) -> tuple[bool, dict[str, Any]]:
        return should_abstain(results, self.abstain_min_top1_score, self.abstain_min_margin, mode=self.abstention_mode)

    def _is_abstention_answer(self, answer: str) -> bool:
        return is_abstention_answer(answer)

    def _salvage_answer_with_extraction(
        self,
        question: str,
        context_chunks: list[dict[str, Any]],
        original: LLMResponse,
    ) -> LLMResponse:
        return salvage_answer_with_extraction(question, context_chunks, original, self.llm)

    def _repair_missing_citations(self, answer: str, results: list[SearchResult]) -> str:
        return repair_missing_citations(answer, results)

    def _assemble_context(
        self, results: list[SearchResult], question: str
    ) -> list[SearchResult]:
        return assemble_context(results, question, keep=self._keep_count())

    def _format_context(self, results: list[SearchResult]) -> list[dict]:
        return format_context(results)

    def _extract_sources(self, results: list[SearchResult]) -> list[dict[str, Any]]:
        return extract_sources(results)

    def _append_debug_trace(self, payload: dict[str, Any]) -> None:
        append_debug_trace(payload, self.debug_trace_path)

    def _retrieve(
        self,
        question: str,
        query_embedding: list[float],
        metadata_filter: dict[str, Any] | None,
        profile: str = "general",
        query_text_alt: str | None = None,
    ) -> list[SearchResult]:
        params = self._profile_params(profile)
        return retrieve(
            question,
            query_embedding,
            metadata_filter,
            vector_store=self.vector_store,
            use_hybrid=self.use_hybrid,
            rrf_k=self.rrf_k,
            ef_search=self.ef_search,
            params=params,
            query_text_alt=query_text_alt,
        )

    def _retrieve_with_debug(
        self,
        question: str,
        query_embedding: list[float],
        metadata_filter: dict[str, Any] | None,
        profile: str = "general",
        include_debug: bool = False,
        query_text_alt: str | None = None,
    ) -> tuple[list[SearchResult], dict[str, Any]]:
        params = self._profile_params(profile)
        return retrieve_with_debug(
            question,
            query_embedding,
            metadata_filter,
            vector_store=self.vector_store,
            use_hybrid=self.use_hybrid,
            rrf_k=self.rrf_k,
            ef_search=self.ef_search,
            params=params,
            include_debug=include_debug,
            query_text_alt=query_text_alt,
        )

    # ── Public API ──────────────────────────────────────────────────────

    def query(
        self,
        question: str,
        conversation_history: list[dict[str, str]] | None = None,
        metadata_filter: dict[str, Any] | None = None,
        return_debug: bool = False,
    ) -> RetrievalResult | tuple[RetrievalResult, dict[str, Any]]:
        """
        Execute a full RAG query: embed → retrieve → generate.

        Args:
            question: The user's question.
            conversation_history: Prior conversation turns for context.
            metadata_filter: Optional filter to narrow search (e.g., by document).
            return_debug: If True, return (result, debug_dict) with retrieval/LLM debug for failing-query diagnosis.

        Returns:
            RetrievalResult, or (RetrievalResult, debug_dict) when return_debug=True.
        """
        logger.info("Processing query", question=question[:100])
        if self._use_baseline():
            return self._query_baseline(
                question=question,
                conversation_history=conversation_history,
                return_debug=return_debug,
            )

        trace: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": question,
            "retrieval_query": question,
            "use_hybrid": self.use_hybrid,
            "use_reranker": self.use_reranker,
            "use_two_pass_answer": self.use_two_pass_answer,
        }
        effective_filter = metadata_filter or self._build_metadata_filter(question)
        debug_out: dict[str, Any] = {
            "tenant_id": getattr(self.vector_store, "tenant_id", None),
            "metadata_filter": effective_filter,
            "doc_ids_filter": effective_filter.get("document_ids") if effective_filter else None,
            "query_text_used": question,
            "abstain_thresholds": {
                "min_top1_score": self.abstain_min_top1_score,
                "min_margin": self.abstain_min_margin,
            },
            "abstain_decision": None,
            "strict_lex_count": None,
            "fallback_lex_count": None,
            "vector_count": None,
            "fused_count": None,
            "pre_rerank_count": None,
            "post_rerank_count": None,
            "final_context_char_length": 0,
            "not_found_trigger": None,
        }

        # 1. Embed the question
        query_embedding = self.embedder.embed_text(question)

        profile = detect_query_profile(question)
        entity_filter = self._build_metadata_filter(question)
        retrieval_query_text = self._build_retrieval_query_text(question, entity_filter, profile)

        # Query rewriting: normalize model numbers, expand error codes for lexical
        retrieval_query_text = normalize_model_number(retrieval_query_text)
        lexical_query_text = expand_error_code(retrieval_query_text)
        query_text_alt = generate_lexical_alt(lexical_query_text)

        # Metadata filter is kept for debug only; never used as a hard SQL filter
        retrieval_filter = None

        # 2. Retrieve (hybrid or dense); request debug when return_debug
        search_results, retrieval_debug = self._retrieve_with_debug(
            retrieval_query_text,
            query_embedding,
            retrieval_filter,
            profile,
            include_debug=self.debug_trace_enabled or return_debug,
            query_text_alt=query_text_alt,
        )
        trace["retrieval_query"] = retrieval_query_text
        if retrieval_debug:
            trace.update(retrieval_debug)
            if return_debug:
                debug_out["strict_lex_count"] = retrieval_debug.get("lexical_strict_hit_count")
                debug_out["fallback_lex_count"] = retrieval_debug.get("lexical_fallback_hit_count")
                debug_out["vector_count"] = retrieval_debug.get("vector_hit_count")
                debug_out["query_text_used"] = retrieval_debug.get("query_text_used", retrieval_query_text)
        fused_count = len(search_results)

        # Fallback: if entity-rewrite produced 0 results, retry with original question
        if fused_count == 0 and retrieval_query_text != question:
            logger.info("Entity-rewrite returned 0 results; retrying with original question")
            fallback_alt = generate_lexical_alt(question)
            search_results, retrieval_debug = self._retrieve_with_debug(
                question,
                query_embedding,
                None,
                profile,
                include_debug=self.debug_trace_enabled or return_debug,
                query_text_alt=fallback_alt,
            )
            fused_count = len(search_results)
            debug_out["entity_rewrite_fallback"] = True
            if retrieval_debug and return_debug:
                debug_out["strict_lex_count"] = retrieval_debug.get("lexical_strict_hit_count")
                debug_out["fallback_lex_count"] = retrieval_debug.get("lexical_fallback_hit_count")
                debug_out["vector_count"] = retrieval_debug.get("vector_hit_count")
                debug_out["query_text_used"] = question

        debug_out["fused_count"] = fused_count
        debug_out["pre_rerank_count"] = fused_count

        if self.debug_trace_enabled:
            trace["fused_results_before_rerank"] = [
                {"id": r.document_id, "score": r.score} for r in search_results
            ]

        # 3. Optional rerank then take top N
        _reranker_produced_valid_scores = False
        if self.use_reranker and self.reranker and search_results:
            passages = [r.text for r in search_results]
            reranked = self.reranker.rerank(question, passages, top_n=self.rerank_top_n)
            # Check if reranker produced valid scores (not NaN)
            import math
            has_valid_scores = reranked and not math.isnan(reranked[0][1])
            _reranker_produced_valid_scores = has_valid_scores
            by_idx = {i: r for i, r in enumerate(search_results)}
            if has_valid_scores:
                reranked_results: list[SearchResult] = []
                for i, rerank_score in reranked:
                    if i not in by_idx:
                        continue
                    base = by_idx[i]
                    base.metadata = dict(base.metadata or {})
                    base.metadata["rrf_score"] = base.score
                    base.metadata["rerank_score"] = float(rerank_score)
                    base.score = float(rerank_score)
                    reranked_results.append(base)
                search_results = reranked_results
            else:
                # NaN scores — keep original RRF order, just trim to top_n
                logger.warning("Reranker returned NaN scores; keeping RRF order")
                search_results = search_results[:self.rerank_top_n]
            if self.debug_trace_enabled:
                trace["reranker_ranked_indices"] = [{"idx": i, "score": s} for i, s in reranked]
        if self.debug_trace_enabled:
            trace["reranked_top_n_chunks"] = [
                {"id": r.document_id, "score": r.score} for r in search_results[: self.rerank_top_n]
            ]
            trace["query_profile"] = profile
            trace["metadata_filter"] = metadata_filter or entity_filter
        # 3b. Fin-Tek boosting: model-number and content-type prioritisation
        search_results = boost_model_number_query(
            question, search_results, model_number_boost=self.model_number_boost,
        )
        search_results = boost_content_type(
            question, search_results, content_type_boost=self.content_type_boost,
        )

        keep = self._keep_count()
        search_results = search_results[:keep]
        debug_out["post_rerank_count"] = len(search_results)

        # 4. No global score threshold (rely on topK + rerank). Optionally filter only if threshold > 0.
        if self.score_threshold > 0:
            relevant_results = [r for r in search_results if r.score >= self.score_threshold]
        else:
            relevant_results = search_results

        def _make_return(result: RetrievalResult) -> RetrievalResult | tuple[RetrievalResult, dict[str, Any]]:
            if return_debug:
                return result, debug_out
            return result

        abstain, abstain_details = self._should_abstain(relevant_results)
        debug_out["abstain_decision"] = abstain_details
        _citations_repaired = False

        # Skip score-based abstention when reranker produced NaN — thresholds
        # are calibrated for reranker scores, not RRF scores.
        if abstain and _reranker_produced_valid_scores:
            # Optional tie-breaker: before abstaining on score thresholds, ask a tiny
            # relevance gate over top chunks. This helps reduce false abstains in demos.
            if self.use_llm_gate_on_abstain and relevant_results:
                gate_chunks = self._format_context(relevant_results[:3])
                is_relevant, gate_raw = llm_relevance_gate(question, gate_chunks, self.llm)
                debug_out["llm_relevance_gate_on_abstain"] = {"relevant": is_relevant, "raw": gate_raw[:100]}
                if is_relevant:
                    logger.info("Abstain overridden by relevance gate")
                    abstain = False

            if abstain:
                debug_out["not_found_trigger"] = "abstain (top1 score or margin below threshold)"
                fallback_messages = [
                    {"role": "user", "content": NO_CONTEXT_GENERAL_PROMPT.format(question=question)},
                ]
                fallback_response = self.llm.generate(fallback_messages)
                return _make_return(RetrievalResult(
                    answer=fallback_response.content,
                    sources=[],
                    model=fallback_response.model,
                    usage=fallback_response.usage,
                    confidence=0.0,
                ))

        # 4b. LLM relevance gate: when reranker scores are unavailable (NaN),
        # use a cheap LLM call to check whether context answers the question.
        if relevant_results and not _reranker_produced_valid_scores:
                # Build quick context preview for the gate
                gate_chunks = self._format_context(relevant_results[:3])
                is_relevant, gate_raw = llm_relevance_gate(question, gate_chunks, self.llm)
                debug_out["llm_relevance_gate"] = {"relevant": is_relevant, "raw": gate_raw[:100]}
                if not is_relevant:
                    debug_out["not_found_trigger"] = "llm_relevance_gate (context not relevant)"
                    logger.info("LLM relevance gate: context not relevant; abstaining")
                    fallback_messages = [
                        {"role": "user", "content": NO_CONTEXT_GENERAL_PROMPT.format(question=question)},
                    ]
                    fallback_response = self.llm.generate(fallback_messages)
                    return _make_return(RetrievalResult(
                        answer=fallback_response.content,
                        sources=[],
                        model=fallback_response.model,
                        usage=fallback_response.usage,
                        confidence=0.0,
                    ))

        if not relevant_results:
            debug_out["not_found_trigger"] = "no relevant_results (search_results empty or score_threshold filtered all)"
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
            return _make_return(RetrievalResult(
                answer=fallback_response.content,
                sources=[],
                model=fallback_response.model,
                usage=fallback_response.usage,
                confidence=0.0,
            ))

        # 5. Manual-aware context assembly (dedupe, prefer procedure/safety/spec)
        assembled = self._assemble_context(relevant_results, question)
        context_chunks = self._format_context(assembled)
        context_str = "\n\n".join(c.get("text", "") for c in context_chunks)
        if return_debug:
            debug_out["final_context_char_length"] = len(context_str)
            debug_out["not_found_trigger"] = "had_context"
        if self.debug_trace_enabled:
            trace["final_context_preview"] = "\n\n".join(c.get("text", "") for c in context_chunks[:2])

        # 6. Generate response (two-pass or single-pass)
        if self.use_two_pass_answer and not self.use_single_pass_fast and context_chunks:
            extract_messages = build_extract_sentences_messages(question, context_chunks)
            extract_response = self.llm.generate(extract_messages)
            extracted_text = extract_response.content.strip()
            compose_messages = build_compose_from_extracted_messages(question, extracted_text)
            compose_response = self.llm.generate(compose_messages)
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
            # If two-pass still produced an abstention, try single-pass as fallback
            if self._is_abstention_answer(llm_response.content) and relevant_results:
                logger.info("Two-pass answer abstained; trying single-pass fallback")
                messages = build_chat_messages(
                    user_question=question,
                    context_chunks=context_chunks,
                    conversation_history=conversation_history,
                )
                single_pass = self.llm.generate(messages)
                if not self._is_abstention_answer(single_pass.content):
                    llm_response = single_pass
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
            if self._is_abstention_answer(llm_response.content) and relevant_results:
                llm_response = self._salvage_answer_with_extraction(question, context_chunks, llm_response)
            if self.debug_trace_enabled:
                trace["assembled_prompt_messages"] = messages
                trace["raw_model_output"] = llm_response.content

        # Must-cite-or-abstain: only for error_codes profile where citation is
        # critical to avoid hallucinated error code explanations.  Spec_lookup is
        # too broad (matches almost every technical question) and was causing
        # false abstentions on good answers.
        # Also run _repair_missing_citations FIRST so the LLM's answer gets a
        # chance to have citations attached before we check.
        llm_response.content = self._repair_missing_citations(llm_response.content, relevant_results)
        _citations_repaired = True  # flag so we don't repair twice below

        if profile == "error_codes" and not _CITATION_PATTERN.search(llm_response.content):
            # Also accept bare [source.pdf] citations (no |p= or |s=)
            _bare_cite = re.search(r"\[[^\]\s]+\.pdf\]", llm_response.content)
            if not _bare_cite:
                # Try salvage: extract+compose may produce citations
                if context_chunks and not self.use_single_pass_fast:
                    salvaged = self._salvage_answer_with_extraction(question, context_chunks, llm_response)
                    if _CITATION_PATTERN.search(salvaged.content) or re.search(r"\[[^\]\s]+\.pdf\]", salvaged.content):
                        llm_response = salvaged
                        logger.info("Error-code query salvaged via extraction (citations found)")
                    else:
                        debug_out["not_found_trigger"] = "must_cite_abstain (error_codes query, no citations after salvage)"
                        logger.info("Error-code query produced no citations after salvage; abstaining")
                        fallback_messages = [
                            {"role": "user", "content": NO_CONTEXT_GENERAL_PROMPT.format(question=question)},
                        ]
                        fallback_response = self.llm.generate(fallback_messages)
                        return _make_return(RetrievalResult(
                            answer=fallback_response.content,
                            sources=[],
                            model=fallback_response.model,
                            usage=fallback_response.usage,
                            confidence=0.0,
                        ))
                else:
                    debug_out["not_found_trigger"] = "must_cite_abstain (error_codes query, no citations)"
                    logger.info("Error-code query produced no citations; abstaining")
                    fallback_messages = [
                        {"role": "user", "content": NO_CONTEXT_GENERAL_PROMPT.format(question=question)},
                    ]
                    fallback_response = self.llm.generate(fallback_messages)
                    return _make_return(RetrievalResult(
                        answer=fallback_response.content,
                        sources=[],
                        model=fallback_response.model,
                        usage=fallback_response.usage,
                        confidence=0.0,
                    ))

        if not _citations_repaired:
            llm_response.content = self._repair_missing_citations(llm_response.content, relevant_results)

        # 7. Extract unique sources
        sources = self._extract_sources(relevant_results)
        avg_score = sum(r.score for r in relevant_results) / len(relevant_results)

        logger.info(
            "Query complete",
            sources=len(relevant_results),
            avg_score=round(avg_score, 3),
            tokens=llm_response.usage.get("total_tokens", 0),
        )
        if self.debug_trace_enabled:
            trace["returned_answer"] = llm_response.content
            trace["sources"] = sources
            self._append_debug_trace(trace)

        return _make_return(RetrievalResult(
            answer=llm_response.content,
            sources=sources,
            model=llm_response.model,
            usage=llm_response.usage,
            confidence=avg_score,
        ))

    # ── Baseline path ──────────────────────────────────────────────────

    def _query_baseline(
        self,
        question: str,
        conversation_history: list[dict[str, str]] | None = None,
        return_debug: bool = False,
    ) -> RetrievalResult | tuple[RetrievalResult, dict[str, Any]]:
        """Minimal path: normalize -> vector search -> top-k -> single prompt -> generate. No rerank/rewrite/abstain."""
        normalized = baseline_normalize_query(question)
        trace: dict[str, Any] = {
            "path": "baseline",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": question,
            "normalized_query": normalized,
            "retrieved_doc_ids": [],
            "retrieved_scores": [],
            "top_k_context_chunk_ids": [],
            "context_char_length": 0,
        }
        results = run_baseline_retrieval(
            self.embedder,
            self.vector_store,
            normalized,
            self.baseline_top_k,
        )
        trace["retrieved_doc_ids"] = [r.document_id for r in results]
        trace["retrieved_scores"] = [r.score for r in results]

        if not results:
            logger.info("Baseline: no results; using no-context response")
            fallback_messages = [
                {"role": "user", "content": NO_CONTEXT_GENERAL_PROMPT.format(question=question)},
            ]
            fallback_response = self.llm.generate(fallback_messages)
            if self.debug_trace_enabled:
                self._append_debug_trace(trace)
            result = RetrievalResult(
                answer=fallback_response.content,
                sources=[],
                model=fallback_response.model,
                usage=fallback_response.usage,
                confidence=0.0,
            )
            if return_debug:
                return result, trace
            return result

        trace["top_k_context_chunk_ids"] = [r.document_id for r in results]
        context_chunks = self._format_context(results)
        context_str = "\n\n".join(c.get("text", "") for c in context_chunks)
        trace["context_char_length"] = len(context_str)

        messages = build_chat_messages(
            user_question=question,
            context_chunks=context_chunks,
            conversation_history=conversation_history,
        )
        llm_response = self.llm.generate(messages)
        sources = self._extract_sources(results)
        avg_score = sum(r.score for r in results) / len(results)

        if self.debug_trace_enabled:
            trace["returned_answer"] = llm_response.content
            trace["sources"] = sources
            self._append_debug_trace(trace)

        result = RetrievalResult(
            answer=llm_response.content,
            sources=sources,
            model=llm_response.model,
            usage=llm_response.usage,
            confidence=avg_score,
        )
        if return_debug:
            return result, trace
        return result

    def _query_baseline_stream(
        self,
        question: str,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> tuple[Iterator[str], list[dict[str, Any]]]:
        """Baseline path for streaming: normalize -> vector search -> top-k -> single prompt -> stream."""
        normalized = baseline_normalize_query(question)
        results = run_baseline_retrieval(
            self.embedder,
            self.vector_store,
            normalized,
            self.baseline_top_k,
        )
        if not results:
            def empty_stream() -> Iterator[str]:
                yield NO_CONTEXT_RESPONSE
            return empty_stream(), []

        context_chunks = self._format_context(results)
        messages = build_chat_messages(
            user_question=question,
            context_chunks=context_chunks,
            conversation_history=conversation_history,
        )
        token_stream = self.llm.stream(messages)
        sources = self._extract_sources(results)
        return token_stream, sources

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
        if self._use_baseline():
            return self._query_baseline_stream(question=question, conversation_history=conversation_history)

        # Keep policy parity with non-streaming path for answer quality:
        # abstention thresholds, gate handling, salvage, and citation repair.
        result = self.query(
            question=question,
            conversation_history=conversation_history,
            metadata_filter=metadata_filter,
        )

        def final_answer_stream() -> Iterator[str]:
            yield result.answer

        return final_answer_stream(), result.sources
