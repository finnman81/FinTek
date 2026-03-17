# RAG Retrieval Tuning — Current State

Last updated: March 17, 2026 (Windows baseline + demo preset + answer-quality hardening + phase 4 iteration)

## Production Readiness Targets (Working)

Use these as practical score targets for release decisions.

### Launch Bar (pilot-safe with guardrails)

| Metric | Target |
|--------|--------|
| Hallucinations | 0 critical (or <1% minor) |
| Faithfulness | >= 0.88 |
| Citation Correct | >= 0.65 |
| Answer Relevance | >= 0.70 |
| Context Recall | >= 0.75 |
| MRR | >= 0.50 |
| nDCG@5 | >= 0.55 |
| Out-of-scope catch rate | >= 0.90 |
| In-scope false-abstain rate | <= 0.15 |

### Target Bar (production-strong)

| Metric | Target |
|--------|--------|
| Hallucinations | 0 sustained |
| Faithfulness | >= 0.93 |
| Citation Correct | >= 0.80 |
| Answer Relevance | >= 0.80 |
| Context Recall | >= 0.85 |
| MRR | >= 0.60 |
| nDCG@5 | >= 0.65 |
| Out-of-scope catch rate | >= 0.95 |
| In-scope false-abstain rate | <= 0.08 |

## Architecture

The RAG pipeline processes queries through these stages:

1. **Hybrid retrieval** — vector search (currently text-embedding-3-small, 1536d) + lexical search (PostgreSQL tsvector) fused via Reciprocal Rank Fusion (RRF)
2. **Reranker** — cross-encoder/ms-marco-MiniLM-L-6-v2 re-scores and reorders results
3. **Fin-Tek boosting** — model number and content type matching boost relevant chunks
4. **Abstention layer** — score-based thresholds + LLM relevance gate decide whether to answer or decline
5. **Two-pass answer generation** — extract relevant sentences with citations, then compose final answer
6. **Must-cite-abstain** — error code queries must produce citations or the system declines
7. **Citation repair** — post-processing attaches citations to uncited factual sentences

## Current Metrics (Windows, 86-question evals)

### A) Windows baseline (full 86, pre-demo preset)

| Metric | Overall | In-Scope (n=64) | Out-of-Scope (n=22) |
|--------|---------|------------------|----------------------|
| Context Recall | 0.593 | — | 0.000 |
| Faithfulness | 0.788 | — | — |
| Citation Correct | 0.097 | — | — |
| Abstention Accuracy | 0.407 | — | — |
| Hallucinations | 0/86 | 0/86 | 0/86 |
| Answer Relevance | 0.547 | — | — |

### B) Windows demo preset (full 86, current recommended demo settings)

| Metric | Overall | Delta vs A |
|--------|---------|------------|
| Context Recall | 0.698 | +0.105 |
| Context Precision | 0.274 | +0.030 |
| MRR | 0.387 | +0.044 |
| nDCG@5 | 0.430 | +0.053 |
| Faithfulness | 0.916 | +0.128 |
| Citation Correct | 0.118 | +0.021 |
| Abstention Accuracy | 0.465 | +0.058 |
| Answer Relevance | 0.555 | +0.008 |
| Hallucinations | 0/86 | unchanged |

### C) Quick validation run (sample 25, demo preset)

| Metric | Value |
|--------|-------|
| Context Recall | 0.640 |
| Faithfulness | 0.836 |
| Citation Correct | 0.233 |
| Abstention Accuracy | 0.680 |
| Answer Relevance | 0.636 |
| Hallucinations | 0/25 |

### D) Windows abstention-logic probe (full 86, demo preset + `use_llm_gate_on_abstain: true`)

This run adds a logic tie-breaker: when score thresholds would abstain, run a small relevance gate and continue only if gate says context is relevant.

| Metric | Overall | Delta vs B |
|--------|---------|------------|
| Context Recall | 0.698 | +0.000 |
| Context Precision | 0.274 | +0.000 |
| MRR | 0.387 | +0.000 |
| nDCG@5 | 0.430 | +0.000 |
| Faithfulness | 0.805 | -0.111 |
| Citation Correct | 0.202 | +0.084 |
| Abstention Accuracy | 0.733 | +0.268 |
| Answer Relevance | 0.591 | +0.036 |
| Hallucinations | 0/86 | unchanged |

Interpretation:
- The abstention logic itself was a major lever on Windows (big abstention-accuracy gain).
- Retrieval ranking quality did not change (identical Layer-1 metrics, as expected).
- Tradeoff observed: higher abstention/citation/relevance, but lower faithfulness.
- Recommendation: this is now adopted as the main working option, with additional safeguards from answer-quality hardening.

### E) Current main option (full 86, answer-quality hardening + phase 4 tweak #1)

This is the currently retained setup after additional validation and rollback of non-holding tweaks:
- `use_llm_gate_on_abstain: true`
- evidence-aware citation repair (no blind top-citation attachment)
- broader abstention phrase detection
- streaming/non-streaming policy parity
- query entity fix: error codes no longer leak into part numbers

| Metric | Overall | Delta vs B |
|--------|---------|------------|
| Context Recall | 0.698 | +0.000 |
| Context Precision | 0.274 | +0.000 |
| MRR | 0.387 | +0.000 |
| nDCG@5 | 0.430 | +0.000 |
| Faithfulness | 0.894 | -0.022 |
| Citation Correct | 0.141 | +0.023 |
| Abstention Accuracy | 0.512 | +0.047 |
| Answer Relevance | 0.577 | +0.022 |
| Hallucinations | 0/86 | unchanged |

### Per-Category Recall

| Category | n | Recall | Abstention Acc |
|----------|---|--------|----------------|
| model_specific | 12 | 1.000 | — |
| cross_model | 10 | 0.900 | — |
| parts_lookup | 10 | 1.000 | — |
| pm_procedure | 10 | 0.900 | — |
| error_code | 11 | 0.909 | — |
| troubleshooting | 11 | 0.909 | — |
| out_of_scope | 22 | 0.000 | — |

## Current Limitations

### 1. Lexical retrieval is still weak (highest remaining gap)

Strict lexical hit rate is very low on this corpus (Windows runs show ~96% lexical zero rate). The system still performs because vector retrieval + reranker are now functioning, but this limits parts/error-code recall headroom.

### 2. Abstention still conservative for some in-scope questions

Even with relaxed demo thresholds, some in-scope queries still abstain despite relevant retrieval (e.g., certain dimensions/spec and troubleshooting prompts).
The current main option improves abstention accuracy versus the original demo preset, but there is still headroom.

### 3. Citation correctness is improved but still low

Citation correctness improved from 0.097 (Windows baseline) to 0.141 (current main option), but still trails production target levels.

### 4. macOS reranker issue remains environment-specific

The prior NaN reranker behavior appears to be macOS-specific; on Windows, reranker loaded and ran normally (CUDA path, no NaN fallback observed).

### 5. Embedding/schema compatibility caveat

Current database schema expects vector(1536). Attempting 3072-d embeddings (`text-embedding-3-large`) caused ingestion failures. Current working config uses `text-embedding-3-small` (1536d).

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

1. **Use current main option as default** — Keep the validated answer-quality hardening and phase 4 tweak #1 on top of the demo preset.

2. **Calibrate abstention thresholds on Windows data** — Sweep `abstain_min_top1_score` and `abstain_min_margin` around current demo values (0.02 / 0.01) to reduce remaining false abstains while preserving OOS behavior.

3. **Target lexical hit-rate improvement** — Continue phase 4 with low-risk lexical/query-rewrite changes and keep only changes that hold on full 86.

### Medium Impact

4. **Tighten relevance-gate prompt before forcing non-abstain** — The logic probe (`use_llm_gate_on_abstain`) improved abstention and citation scores but reduced faithfulness. Refine gate criteria (require stronger topical/evidence match) to preserve the abstention gain while recovering faithfulness.

5. **Citation-focused prompt pass** — Add explicit “retain original citation bracket format exactly” instructions and verify against eval matcher format.

6. **Optional demo latency trim** — If response speed is more important than thoroughness, reduce `vector_top_k` from 40 to ~35 while keeping `final_k` 25 and reranker on; recheck abstention and relevance.

7. **Stability pass for timeouts** — Keep API/network timeout monitoring in eval runs; occasional timeout-driven failures can skew answer-quality metrics.

### Lower Priority

8. **Try alternative reranker models** — `cross-encoder/ms-marco-MiniLM-L-12-v2` or `BAAI/bge-reranker-base` may improve parts/spec ranking quality.

9. **Embedding model comparison** — Keep within 1536-d schema constraints unless schema migration is planned.

10. **Query rewriting improvements** — The entity extraction for error codes sometimes misclassifies part numbers (e.g., "E02" extracted as both error code and part number). Tightening the regex patterns would reduce noise in the retrieval query.

## Eval Version History

| Version | Key Change | Abstention Acc | Faithfulness | Notes |
|---------|-----------|----------------|--------------|-------|
| v1 | Baseline (vector-only path) | 0.453 | 0.844 | 96.5% lexical zero rate |
| v3 | OR-fallback lexical | 0.453 | 0.845 | Lexical zero → 2.3%, recall dropped |
| v4 | Full pipeline + tighter thresholds | 0.663 | 0.753 | must-cite-abstain too aggressive |
| v5 | Narrowed must-cite to error_codes only | 0.709 | 0.807 | Best abstention before gate |
| v6c | LLM relevance gate + NaN handling | 0.605 | 0.886 | 19/22 OOS caught, reranker broken |
| v7 | Compose prompt tweak (reverted) | 0.488 | 0.884 | Prompt change hurt, reverted to v6c |
| v8-win-base | Windows full baseline (86) | 0.407 | 0.788 | Reranker healthy; conservative abstention + timeouts |
| v9-win-demo | Windows demo preset full (86) | 0.465 | 0.916 | Best current demo profile, zero hallucinations |
| v10-win-gate | Demo preset + gate override on abstain | 0.733 | 0.805 | Big abstention gain, but faithfulness dropped |
| v11-win-main | Main option with answer-quality hardening | 0.512 | 0.891 | Better balance: citation/abstention/relevance up vs demo preset |
| v12-win-phase4-keep | Phase 4 tweak #1 retained | 0.512 | 0.894 | Error code/part separation fix; slight citation + faithfulness gain |
