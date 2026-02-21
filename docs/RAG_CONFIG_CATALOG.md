# RAG Config Catalog

Catalog of retrieval-related configuration. Source of truth: `RetrievalConfig` in `src/core/config.py` and `config/settings.yaml` under `retrieval:`. Environment variables that affect retrieval: none in `_apply_env_overrides` today; `RAG_DEBUG_TRACE` and `RAG_DEBUG_TRACE_PATH` are read in `RetrievalEngine.__init__` for debug tracing.

## Classification

- **baseline**: Used by the minimal baseline path (vector-only, top-k, single prompt).
- **advanced**: Used by the full path (hybrid, rerank, query rewrite, two-pass, abstain, etc.).
- **deprecated**: To be removed or already unused.
- **unknown**: Unclear; document for follow-up.

## RetrievalConfig fields

| Config key | Purpose | Classification | Code path |
|------------|---------|----------------|-----------|
| `top_k` | Number of chunks for dense-only retrieval and context when not using hybrid/rerank. | baseline | `engine.query`, `engine.query_stream` (dense path and final keep count) |
| `score_threshold` | Minimum score for a chunk to be included; 0 = disabled. | baseline | `engine.query`, `engine.query_stream` (filter `relevant_results`) |
| `include_metadata` | Whether to include metadata in responses. | unknown | Not directly used in engine; may be used by API/serialization. |
| `use_hybrid` | If true, use hybrid (vector + lexical) search with RRF fusion. | advanced | `engine.query`, `engine.query_stream` (`_retrieve`, `_retrieve_with_debug`) |
| `vector_top_k` | Candidates from vector search in hybrid. | advanced | `engine.query`, `engine.query_stream` (hybrid path) |
| `lexical_top_k` | Candidates from lexical search in hybrid. | advanced | `engine.query`, `engine.query_stream` (hybrid path) |
| `rrf_k` | RRF constant for reciprocal rank fusion. | advanced | `engine.query`, `engine.query_stream` (hybrid path) |
| `final_k` | Number of fused candidates before rerank in hybrid. | advanced | `engine.query`, `engine.query_stream` (hybrid path) |
| `ef_search` | HNSW ef_search for vector search (pgvector). | advanced | Hybrid search in pgvector_store |
| `rerank_top_n` | Number of passages to return from reranker. | advanced | `engine.query`, `engine.query_stream` (rerank path) |
| `final_context_chunks` | Chunks kept after rerank (or after hybrid) for context. | advanced | `engine.query`, `engine.query_stream` (keep count) |
| `use_two_pass_answer` | If true, extract sentences then compose (two LLM calls). | advanced | `engine.query` only |
| `use_reranker` | If true, run cross-encoder reranker before context assembly. | advanced | `engine.query`, `engine.query_stream` |
| `reranker_model` | Cross-encoder model name; empty = default. | advanced | `deps.py` when instantiating `CrossEncoderReranker` |
| `abstain_min_top1_score` | Minimum top-1 score or abstain. | advanced | `engine.query` (`_should_abstain`) |
| `abstain_min_margin` | Minimum top1-top2 margin or abstain. | advanced | `engine.query` (`_should_abstain`) |

## Query-rewrite and profile behavior

Not separate config keys; behavior is driven by code in `engine.py` and `query_rewrite.py`:

- **Profile** (`detect_query_profile`): affects `_profile_params` (different top_k/vector_top_k/lexical_top_k/final_k for `error_codes`, `spec_lookup`, `procedures`, `troubleshooting`) and `_build_retrieval_query_text` (entity-focused query for spec/error).
- **Entity filter** (`extract_query_entities`): used in `_build_metadata_filter`; filter is not applied as hard SQL filter but can affect debug and fallback.
- **Lexical alt** (`generate_lexical_alt`): alternative query for hybrid lexical branch.

Classification: **advanced** (all of the above).

## Environment variables (retrieval / RAG)

| Env var | Purpose | Classification |
|---------|---------|----------------|
| `RAG_DEBUG_TRACE` | If `"1"`, append trace JSON to `RAG_DEBUG_TRACE_PATH`. | baseline/advanced (observability) |
| `RAG_DEBUG_TRACE_PATH` | Path to JSONL file for trace output. | baseline/advanced (observability) |
| `RAG_FORCE_BASELINE` | If `"1"`, force baseline path regardless of config (Phase 1). | baseline (kill-switch) |

## Phase 1 additions (baseline path)

| Config key | Purpose | Classification |
|------------|---------|----------------|
| `use_baseline_path` | If true, use minimal baseline pipeline (vector-only, no rerank/rewrite). Default true. | baseline |
| `baseline_top_k` | Top-k for baseline path only. | baseline |
