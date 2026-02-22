# RAG Evaluation Harness (Phase 2)

Locked query set and runner for measuring retrieval and answer quality. Used to establish a baseline and to gate Phase 3 feature reintroduction.

## Files

| File | Purpose |
|------|---------|
| `queries.json` | Locked eval set: 30 queries (10 easy / 10 medium / 10 hard). Do not change without team sign-off. |
| `baseline_metrics.json` | Snapshot of aggregates from a designated baseline run. Committed for comparison. |
| `run_YYYYMMDD_HHMMss.json` | Per-run full results (optional; path set by `--output`). |

## Query schema (`queries.json`)

Each entry:

```json
{
  "id": "e01",
  "difficulty": "easy",
  "question": "...",
  "expected_doc_keywords": ["valve", "priming"],
  "expected_answer_keywords": ["open valve A"],
  "notes": "..."
}
```

- **id**: Unique id (e.g. e01–e10, m01–m10, h01–h10).
- **difficulty**: `easy` | `medium` | `hard`.
- **question**: Exact query string sent to the engine.
- **expected_doc_keywords**: Optional. For recall@k: at least one retrieved chunk must contain at least one of these words (case-insensitive).
- **expected_answer_keywords**: Optional. For answer accuracy: the model answer must contain all of these words (case-insensitive).
- **notes**: Optional human note.

Queries without `expected_doc_keywords` or `expected_answer_keywords` still run and contribute to latency and counts; they are excluded from recall/answer aggregates.

## How to run

From project root, with `.env` set (e.g. `DATABASE_URL`, `OPENAI_API_KEY`, `DEFAULT_TENANT_ID`):

```bash
# Default: top_k=5, output to eval/run_YYYYMMDD_HHMMss.json
python scripts/run_eval.py

# Custom top_k and output path
python scripts/run_eval.py --top-k 5 --output eval/run_20250222.json

# Write baseline snapshot (overwrites eval/baseline_metrics.json)
python scripts/run_eval.py --baseline
```

The runner forces the baseline RAG path (`RAG_FORCE_BASELINE=1`), uses the real DB, embedder, and LLM, and prints a short summary to stdout.

## Metrics

- **recall_at_k**: Fraction of queries that have `expected_doc_keywords` and for which at least one retrieved chunk contains at least one of those keywords.
- **answer_accuracy**: Fraction of queries that have `expected_answer_keywords` and for which the answer contains all of those keywords.
- **latency_p50_ms**, **latency_p95_ms**: 50th and 95th percentile latency (ms) per query.

Aggregates are also broken down by `difficulty` (easy / medium / hard).

## Promotion thresholds (Phase 3 gate)

Before promoting a new retrieval feature (e.g. reranker, hybrid, query rewrite):

- **Recall@k**: Must not drop below baseline by more than **5%**.
- **Answer accuracy**: Must not drop below baseline by more than **5%**.
- **Latency p95**: Must not regress by more than **500 ms**.

If a feature fails these gates twice in a row, it is archived and the next candidate is tried.

## Comparing a run to baseline

1. Run with `--baseline` once to create `eval/baseline_metrics.json`.
2. For a branch or config change, run `python scripts/run_eval.py --output eval/run_branch.json`.
3. Compare `run_branch.json` aggregates (and optionally `by_difficulty`) to `eval/baseline_metrics.json` manually or via a small script.

Future work: add a `--compare eval/baseline_metrics.json` flag to the runner to print a diff.
