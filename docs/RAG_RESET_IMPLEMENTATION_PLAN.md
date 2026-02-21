# RAG Reset Implementation Plan (Back to Basics)

## Objective
Stabilize retrieval quality by replacing the current "black box" pipeline with a minimal, transparent baseline and then reintroducing advanced features one at a time behind measurable gates.

## Guiding Principles
- **One change at a time**: only a single retrieval feature change per iteration.
- **Keep baseline always runnable**: maintain a simple fallback pipeline throughout all phases.
- **Measure before/after**: no feature promotion without quantitative improvement.
- **Prefer visibility over sophistication**: every stage must produce debuggable artifacts.

## Scope Reset (What to temporarily remove)
Freeze or disable the following until baseline metrics are stable:
- Layered retrieval/reranking chains.
- Dynamic query rewriting variants.
- Fusion strategies beyond one simple retrieval mode.
- Experimental weighting schemes and tenant-specific tuning overrides.

Implementation approach:
- Gate each advanced behavior behind explicit config flags.
- Default all advanced flags to `false` in non-experimental environments.

## Target Baseline Architecture (Phase 1 end-state)
A minimal RAG path with explicit observability:
1. **Query normalization** (light cleaning only).
2. **Single retrieval strategy** (choose one: lexical *or* vector; do not combine yet).
3. **Top-k context assembly** with deterministic ordering.
4. **LLM answer generation** with fixed prompt template.
5. **Structured trace output** for each step.

No reranker, no fusion, no query expansion, no post-retrieval heuristic stack.

## Phased Implementation Plan

### Phase 0 — Inventory and Freeze 
**Goal:** Stop ongoing drift and document current behavior.

Tasks:
- Create a current-state map of retrieval flow (entrypoint → retrieval calls → filters → rerank → prompt input).
- List all config switches affecting retrieval and generation.
- Mark each switch as: `baseline`, `advanced`, `deprecated`, or `unknown`.
- Freeze new retrieval feature work until Phase 2.

Deliverables:
- Pipeline map diagram (or markdown call flow).
- Config catalog with owner and purpose.
- Freeze note in team channel + issue tracker.

**Phase 0 freeze (in effect):** New retrieval feature work (layered retrieval, new fusion strategies, new query rewriting, new rerank strategies) is frozen until Phase 2. Use the baseline path for production until baseline metrics are stable. See [RAG_PIPELINE_MAP.md](RAG_PIPELINE_MAP.md) and [RAG_CONFIG_CATALOG.md](RAG_CONFIG_CATALOG.md) for current flow and config. Enforce via PR checklist or issue tracker: link changes that touch retrieval to the "RAG Reset" epic and ensure single-feature changes only when reintroducing features.

### Phase 1 — Build Clean Baseline Path 
**Goal:** Ship a simple, understandable pipeline as the default execution path.

Tasks:
- Implement a dedicated baseline retrieval function/module with no optional layering.
- Route production/default traffic through baseline path.
- Add deterministic, compact debug trace object:
  - normalized query
  - retrieved doc IDs and scores
  - selected top-k context chunks
  - final prompt context length/token estimate
- Add a hard kill-switch to force baseline path even if advanced flags are on.

Acceptance criteria:
- End-to-end queries run without touching advanced components.
- Trace confirms only baseline stages are executed.
- Existing critical smoke tests pass.

### Phase 2 — Establish Evaluation Harness and Guardrails 
**Goal:** Make performance changes measurable and repeatable.

Tasks:
- Lock a representative eval set (small, medium, hard queries).
- Define core metrics:
  - retrieval recall@k
  - context precision proxy (if available)
  - answer correctness/groundedness score
  - latency p50/p95
- Add a standard evaluation command that outputs JSON + text summary.
- Define promotion thresholds (minimum delta required to keep a change).

Acceptance criteria:
- Same commit + same data gives stable metrics within expected variance.
- CI/manual check can compare current branch vs baseline benchmark artifact.

### Phase 3 — Reintroduce Advanced Features Sequentially (ongoing)
**Goal:** Add complexity only when it proves value.

Process per feature:
1. Pick exactly one candidate feature (e.g., reranker).
2. Enable behind feature flag (default off).
3. Run A/B evaluation vs baseline.
4. Keep only if thresholds are met and no major latency regression.
5. Document outcome in "feature decision log."

Suggested reintroduction order:
1. Lightweight reranking.
2. Query rewrite (single controlled strategy).
3. Hybrid fusion.
4. Dynamic weighting/personalization.

Rollback rule:
- If feature fails thresholds twice consecutively, archive it and move to next item.

### Phase 4 — Hardening and Operationalization (after 2–3 successful features)
**Goal:** Ensure maintainability and production reliability.

Tasks:
- Add regression tests for accepted features.
- Add dashboards/alerts for retrieval quality and latency drift.
- Clean dead code and remove deprecated switches.
- Update architecture docs to reflect final supported paths.

## Ownership Model
- **RAG Owner**: decides keep/remove per feature after evaluation.
- **Eval Owner**: maintains datasets, scoring scripts, and benchmark artifacts.
- **Platform Owner**: ensures flags, tracing, and observability wiring remain consistent.

## Operating Cadence
- Daily 15-minute tuning standup during reset period.
- Twice-weekly review of metric trends and feature decisions.
- Weekly "complexity audit": identify anything that bypasses baseline safeguards.

## Risks and Mitigations
- **Risk:** Team reintroduces multiple features simultaneously.  
  **Mitigation:** PR template checkbox enforcing single-feature change policy.
- **Risk:** Metrics are noisy, leading to false decisions.  
  **Mitigation:** fixed eval subsets + repeated runs + confidence bands.
- **Risk:** Hidden dependencies on removed layers.  
  **Mitigation:** keep fallback adapters temporarily, then remove after burn-in.

## Exit Criteria for Reset Initiative
The reset is complete when:
- Baseline path is stable and observable in production.
- At least one advanced feature is reintroduced with clear metric improvement.
- Deprecated legacy paths are removed or permanently disabled.
- Team can explain retrieval behavior from logs without code spelunking.

## Immediate Next 5 Actions
1. Create a "RAG Reset" epic with Phase 0–4 tickets.
2. Add/confirm feature flags for all advanced retrieval behaviors.
3. Implement and route a clean baseline path.
4. Finalize locked eval set + baseline benchmark artifact.
5. Start first reintroduction experiment (reranker) only after baseline sign-off.
