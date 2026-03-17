# RAG Retrieval Tuning — Current State

Last updated: March 16, 2026 (v6c eval)

## Architecture

The RAG pipeline processes queries through these stages:

1. **Hybrid retrieval** — vector search (text-embedding-3-large, 3072d) + lexical search (PostgreSQL tsvector) fused via Reciprocal Rank Fusion (RRF)
2. **Reranker** — cross-encoder/ms-marco-MiniLM-L-6-v2 re-scores and reorders results
3. **Fin-Tek boosting** — model number and content type matching boost relevant chunks
4. **Abstention layer** — score-based thresholds + LLM relevance gate decide whether to answer or decline
5. **Two-pass answer generation** — extract relevant sentences with citations, then compose final answer
6. **Must-cite-abstain** — error code queries must produce citations or the system declines
7. **Citation repair** — post-processing attaches citations to uncited factual sentences

## Current Metrics (v6c, macOS, 86-question eval)

| Metric | Overall | In-Scope (n=64) | Out-of-Scope (n=22) |
|--------|---------|------------------|----------------------|
| Context Recall | 0.442 | 0.594 | 0.000 |
| Faithfulness | 0.886 | 0.870 | 0.932 |
| Citation Correct | 0.093 | 0.125 | 0.000 |
| Abstention Accuracy | 0.605 | 0.516 | 0.864 (19/22) |
| Hallucinations | 0/86 | 0/86 | 0/86 |
| Answer Relevance | 0.583 | 0.697 | 0.250 |

### Per-Category Recall

| Category | n | Recall | Abstention Acc |
|----------|---|--------|----------------|
| model_specific | 12 | 0.833 | 0.667 |
| cross_model | 10 | 0.600 | 0.600 |
| parts_lookup | 10 | 0.600 | 0.600 |
| pm_procedure | 10 | 0.600 | 0.400 |
| error_code | 11 | 0.455 | 0.455 |
| troubleshooting | 11 | 0.455 | 0.364 |
| out_of_scope | 22 | 0.000 | 0.864 |

## Current Limitations

### 1. Broken reranker on macOS (critical, environment-specific)

The cross-encoder reranker produces NaN scores on macOS due to a PyTorch SDPA (Scaled Dot Product Attention) bug with torch 2.7.1 on Apple Silicon. This causes:

- Chunk ordering relies on RRF scores only (no reranking)
- Score-based abstention is bypassed (thresholds calibrated for reranker scores)
- The LLM relevance gate compensates but only sees top chunks by RRF order
- In-scope false abstentions (~48%) because the gate sees wrong chunks at the top

**This resolves on Windows/Linux/AWS** where PyTorch SDPA works correctly. The code has defensive handling: NaN detection in the reranker, automatic fallback to RRF order, and the LLM relevance gate as a safety net.

### 2. Context recall ceiling (0.442 overall, 0.594 in-scope)

The retrieval layer finds the right documents ~60% of the time for in-scope questions. The 22 out-of-scope questions (which correctly have 0.0 recall) drag the overall average to 0.442. Improving this requires better chunking strategies or embedding model tuning for the specific Fin-Tek manual corpus.

### 3. Citation correctness is low (0.093)

The two-pass extract+compose pipeline produces citations in `[source|p=N|s=Section]` format, but:
- The compose step sometimes drops or reformats citations from the extract step
- The eval compares citations against `expected_sources` which may not match the exact format
- Without the reranker, the best chunks aren't always in the context, so citations reference less relevant sources

### 4. Lexical search limitations

Strict lexical search (`websearch_to_tsquery`) produces AND queries that miss industrial manual content where specs are split across chunks. An OR-fallback was added but capped at 10 results to avoid flooding RRF with noise. The lexical zero rate dropped from 96.5% to 2.3% but recall didn't improve proportionally.

## Key Files

| File | Purpose |
|------|---------|
| `src/retrieval/engine.py` | Main RAG pipeline — retrieval, rerank, abstention, answer generation |
| `src/retrieval/abstention.py` | Score-based abstention + LLM relevance gate |
| `src/retrieval/reranker.py` | Cross-encoder reranker with NaN detection |
| `src/retrieval/vector_retrieval.py` | Hybrid search, RRF fusion, Fin-Tek boosting |
| `src/retrieval/query_rewrite.py` | Query profiling, entity extraction, model number normalization |
| `src/llm/prompts.py` | System prompt, extract/compose prompts, citation format |
| `src/vectorstore/pgvector_store.py` | PostgreSQL hybrid search SQL (strict + fallback lexical) |
| `config/settings.yaml` | All tunable parameters (thresholds, top-k, boost factors) |
| `scripts/eval_comprehensive.py` | 3-layer eval framework (retrieval, answer quality, robustness) |
| `eval/datasets/fintek_gold.yaml` | 86-question gold standard eval dataset |

## Suggested Next Steps

### High Impact (do first)

1. **Verify reranker on Windows/AWS** — Run the eval on a non-macOS environment. If the reranker produces valid scores, score-based abstention will work and in-scope abstention accuracy should jump significantly. Run: `bash scripts/run_eval_v6c.sh` (or equivalent).

2. **Calibrate abstention thresholds** — Once the reranker works, run `python -m scripts.calibrate_abstention` to find optimal `abstain_min_top1_score` and `abstain_min_margin` values for the actual reranker score distribution. Current values (0.10 / 0.05) were set blind.

3. **Re-ingest with tuned chunking** — The parent-child chunking (250-word children) was optimized offline but some manuals have tables and spec sheets that don't chunk well. Review the low-recall categories (error_code, troubleshooting) and consider manual-specific chunking rules.

### Medium Impact

4. **Improve citation correctness** — The compose prompt could be more explicit about preserving exact citation brackets. Also consider running citation repair before the must-cite-abstain check (already done in v5+) and validating that the repair function matches the eval's expected format.

5. **Tune the LLM relevance gate** — The gate currently uses 5 chunks at 500 chars each. On AWS with the reranker working, the top 5 chunks will be much more relevant, so the gate should be more accurate. Consider making it configurable via settings.yaml.

6. **Expand eval dataset** — The current 86 questions have 22 out-of-scope (25%) which heavily weights OOS detection. Adding more in-scope questions from real user queries would give a more balanced picture.

### Lower Priority

7. **Try alternative reranker models** — `cross-encoder/ms-marco-MiniLM-L-12-v2` (larger) or `BAAI/bge-reranker-base` may perform better on technical content. The eval framework supports this via `scripts/eval_rerankers.py`.

8. **Embedding model comparison** — Currently using text-embedding-3-large (3072d). Could test text-embedding-3-small or domain-specific models. Run `scripts/eval_embeddings.py`.

9. **Query rewriting improvements** — The entity extraction for error codes sometimes misclassifies part numbers (e.g., "E02" extracted as both error code and part number). Tightening the regex patterns would reduce noise in the retrieval query.

## Eval Version History

| Version | Key Change | Abstention Acc | Faithfulness | Notes |
|---------|-----------|----------------|--------------|-------|
| v1 | Baseline (vector-only path) | 0.453 | 0.844 | 96.5% lexical zero rate |
| v3 | OR-fallback lexical | 0.453 | 0.845 | Lexical zero → 2.3%, recall dropped |
| v4 | Full pipeline + tighter thresholds | 0.663 | 0.753 | must-cite-abstain too aggressive |
| v5 | Narrowed must-cite to error_codes only | 0.709 | 0.807 | Best abstention before gate |
| v6c | LLM relevance gate + NaN handling | 0.605 | 0.886 | 19/22 OOS caught, reranker broken |
| v7 | Compose prompt tweak (reverted) | 0.488 | 0.884 | Prompt change hurt, reverted to v6c |
