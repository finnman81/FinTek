# RAG System Review + Implemented Improvements (P0/P1)

## What changed in this PR
This PR moves from recommendations to implementation for P0 and key P1 items.

### Implemented P0
1. **Eval dataset quality controls**
   - `scripts/generate_questions_300.py` now supports corpus-aware validation via manual manifest.
   - New flags:
     - `--validate-corpus`
     - `--manifest <path>`
   - Generated items now include `should_abstain` labels when entities appear unanswerable from manifest metadata.

2. **Tighter retrieval context packing**
   - Retrieval defaults tuned down to reduce context noise:
     - `lexical_top_k`: `40 -> 30`
     - `final_k`: `20 -> 14`
     - `rerank_top_n`: `30 -> 20`
     - `final_context_chunks`: `8 -> 5`
   - Updated in both config dataclass defaults and `config/settings.yaml`.

3. **Metadata-aware retrieval filtering**
   - Added query entity extraction for error codes / part numbers.
   - Retrieval now builds a metadata filter from query entities and passes filter into dense + hybrid pgvector search.
   - Pgvector SQL now supports array overlap filters on `error_codes` and `part_numbers` and exact filter for `content_type`.

4. **Per-category retrieval profiles**
   - Added query profiling (error_codes/spec/procedures/troubleshooting/safety/general).
   - Retrieval candidate sizes are adjusted by profile to improve precision for code/spec lookup while preserving recall for procedural queries.

### Implemented P1
5. **Calibrated abstention policy**
   - Added score-based abstention controls in retrieval config and engine:
     - `abstain_min_top1_score`
     - `abstain_min_top1_top3_ratio`
   - If confidence is too low and ranking separation is weak, engine abstains safely.

6. **Citation reliability pass**
   - Added post-generation citation repair step in retrieval engine.
   - If answer has no bracket citations but has retrieved context, answer lines are auto-suffixed with top citation bracket.

7. **Testing/eval script improvements**
   - `scripts/eval_comprehensive.py` abstention check now correctly fails when model abstains on answerable items.
   - Added average latency output in retrieval summary for easier trade-off analysis.

---

## Current state after implementation
Architecture now includes:
- Hybrid + rerank retrieval with intent-aware parameterization.
- Metadata-aware filtering for part/error lookups.
- Score-calibrated abstention instead of prompt-only abstention.
- Citation repair safety net.
- Better eval-set labeling support.

These changes target your largest current bottlenecks:
- Low precision from over-broad context.
- Misleading eval outcomes from unlabeled unanswerables.
- Citation reliability drift.

---

## How to test

### 1) Generate improved eval set
```bash
python scripts/generate_questions_300.py \
  --output claw_manuals/eval_questions_300.json \
  --manifest claw_manuals/root/claw_manuals/manual_index.json \
  --validate-corpus
```

### 2) Run comprehensive eval
```bash
python scripts/eval_comprehensive.py \
  --tenant-slug claw-demo \
  --questions claw_manuals/eval_questions_300.json \
  --layer all \
  --output results/
```

### 3) Optional retrieval-only quick check
```bash
python scripts/eval_retrieval.py \
  --tenant claw-demo \
  --questions claw_manuals/eval_questions_300.json
```

### 4) Optional tuning sweep
```bash
python scripts/tune_retrieval.py \
  --tenant claw-demo \
  --questions claw_manuals/eval_questions_300.json \
  --hybrid
```

---

## P2 and beyond (next priorities)
1. **Reranker diagnostics by category**
   - Add score distribution histograms and failure slices per intent class.
2. **Domain gold sets**
   - Build human-verified Q/A/citation sets per customer vertical.
3. **Online learning loop**
   - Capture thumbs up/down + corrected intent to mine hard negatives.
4. **Citation verifier**
   - Span-level citation validation (claim-to-source match).
5. **Operational SLOs**
   - Track p50/p95 latency, citation correctness, abstain rate, and unresolved rate.

---

## Files changed for this implementation
- `src/retrieval/query_rewrite.py`
- `src/retrieval/engine.py`
- `src/vectorstore/pgvector_store.py`
- `src/core/config.py`
- `config/settings.yaml`
- `src/api/deps.py`
- `src/ui/app.py`
- `scripts/generate_questions_300.py`
- `scripts/eval_comprehensive.py`
