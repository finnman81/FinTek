"""
Phase 2 eval runner: run locked query set through the real RAG stack (baseline path),
compute recall@k, answer accuracy, latency; write JSON results and optional baseline snapshot.

Usage (from project root):
  python scripts/run_eval.py [--top-k 5] [--output eval/run_YYYYMMDD.json] [--baseline]

Requires: .env with DATABASE_URL, OPENAI_API_KEY, DEFAULT_TENANT_ID.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Project root and .env
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

# Force baseline path for reproducible eval
os.environ["RAG_FORCE_BASELINE"] = "1"


def _relpath(path: Path, base: Path) -> str:
    try:
        return str(path.resolve().relative_to(base.resolve()))
    except ValueError:
        return str(path)


def _load_queries(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else data.get("queries", [])


def _recall_hit(retrieved_texts: list[str], keywords: list[str]) -> bool:
    if not keywords or not retrieved_texts:
        return True  # no constraint = pass
    text_lower = " ".join(retrieved_texts).lower()
    return any(kw.lower() in text_lower for kw in keywords)


_REFUSAL_MARKERS = (
    "not found in provided documents",
    "no relevant passages",
    "not available in the provided context",
)


def _answer_hit(answer: str, keywords: list[str]) -> bool:
    if not keywords:
        return True
    answer_lower = answer.lower()
    if any(marker in answer_lower for marker in _REFUSAL_MARKERS):
        return False
    return all(kw.lower() in answer_lower for kw in keywords)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run RAG eval set and output metrics.")
    parser.add_argument("--top-k", type=int, default=5, help="Baseline top_k (default 5)")
    parser.add_argument("--output", type=str, default="", help="Output JSON path (default eval/run_YYYYMMDD_HHMMss.json)")
    parser.add_argument("--baseline", action="store_true", help="Also write eval/baseline_metrics.json")
    parser.add_argument("--queries", type=str, default="", help="Path to queries JSON (default eval/queries.json)")
    args = parser.parse_args()

    queries_path = Path(args.queries) if args.queries else ROOT / "eval" / "queries.json"
    if not queries_path.is_file():
        print(f"Queries file not found: {queries_path}", file=sys.stderr)
        return 1

    eval_dir = ROOT / "eval"
    eval_dir.mkdir(parents=True, exist_ok=True)
    if not args.output:
        from datetime import datetime
        args.output = eval_dir / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out_path = Path(args.output)

    tenant_id = os.environ.get("DEFAULT_TENANT_ID", "").strip()
    if not tenant_id:
        print("DEFAULT_TENANT_ID not set in .env", file=sys.stderr)
        return 1

    # Build real stack
    from src.core.config import load_config
    from src.db.connection import get_session_factory
    from src.db.models import Tenant
    from src.llm.factory import create_llm_provider, create_embedding_provider
    from src.vectorstore.pgvector_store import PostgresVectorStore
    from src.retrieval.engine import RetrievalEngine
    from uuid import UUID

    config = load_config()
    factory = get_session_factory()
    session = factory()
    try:
        tid = UUID(tenant_id)
        tenant = session.query(Tenant).filter(Tenant.id == tid).first()
        if not tenant:
            print(f"Tenant {tenant_id} not found.", file=sys.stderr)
            return 1
    finally:
        session.close()

    llm = create_llm_provider(config.llm)
    embedder = create_embedding_provider(config.embedding)
    store = PostgresVectorStore(
        tenant_id=tenant_id,
        session_factory=factory,
        embedding_model=config.embedding.model,
        embedding_version=1,
    )
    top_k = getattr(config.retrieval, "baseline_top_k", 5)
    if args.top_k != 5:
        top_k = args.top_k
    engine = RetrievalEngine(
        llm_provider=llm,
        embedding_provider=embedder,
        vector_store=store,
        top_k=config.retrieval.top_k,
        score_threshold=config.retrieval.score_threshold,
        use_baseline_path=True,
        baseline_top_k=top_k,
    )

    queries = _load_queries(queries_path)
    print(f"Running {len(queries)} queries (baseline top_k={top_k})...")

    results: list[dict] = []
    for i, q in enumerate(queries):
        qid = q.get("id", f"q{i+1}")
        question = q.get("question", "")
        expected_doc = q.get("expected_doc_keywords") or []
        expected_ans = q.get("expected_answer_keywords") or []

        t0 = time.perf_counter()
        try:
            out = engine.query(question, return_debug=True)
            if isinstance(out, tuple):
                result, debug = out
            else:
                result = out
                debug = {}
        except Exception as e:
            results.append({
                "id": qid,
                "difficulty": q.get("difficulty", ""),
                "question": question,
                "error": str(e),
                "latency_ms": int((time.perf_counter() - t0) * 1000),
                "recall_hit": None,
                "answer_hit": None,
                "confidence": None,
                "answer_preview": None,
            })
            continue

        latency_ms = int((time.perf_counter() - t0) * 1000)
        retrieved_texts = debug.get("retrieved_texts") or []
        scores = debug.get("retrieved_scores") or []
        recall_hit = _recall_hit(retrieved_texts, expected_doc) if expected_doc else None
        answer_hit = _answer_hit(result.answer or "", expected_ans) if expected_ans else None

        retrieved_docs = []
        for j, t in enumerate(retrieved_texts):
            s = scores[j] if j < len(scores) else None
            retrieved_docs.append({"text_preview": (t[:200] + "...") if len(t) > 200 else t, "score": s})

        results.append({
            "id": qid,
            "difficulty": q.get("difficulty", ""),
            "question": question,
            "latency_ms": latency_ms,
            "retrieved_docs": retrieved_docs,
            "recall_hit": recall_hit,
            "answer_hit": answer_hit,
            "confidence": result.confidence,
            "answer_preview": (result.answer or "")[:300],
        })

    # Aggregates
    with_recall = [r for r in results if r.get("recall_hit") is not None and "error" not in r]
    with_answer = [r for r in results if r.get("answer_hit") is not None and "error" not in r]
    latencies = [r["latency_ms"] for r in results if "error" not in r]

    recall_at_k = (sum(1 for r in with_recall if r["recall_hit"]) / len(with_recall)) if with_recall else None
    answer_accuracy = (sum(1 for r in with_answer if r["answer_hit"]) / len(with_answer)) if with_answer else None
    latencies_sorted = sorted(latencies) if latencies else []
    n = len(latencies_sorted)
    latency_p50 = latencies_sorted[n // 2] if n else None
    latency_p95 = latencies_sorted[int(n * 0.95)] if n else None

    by_difficulty: dict[str, dict] = {}
    for d in ("easy", "medium", "hard"):
        sub = [r for r in results if r.get("difficulty") == d and "error" not in r]
        rec = [r for r in sub if r.get("recall_hit") is not None]
        ans = [r for r in sub if r.get("answer_hit") is not None]
        by_difficulty[d] = {
            "count": len(sub),
            "recall_at_k": (sum(1 for r in rec if r["recall_hit"]) / len(rec)) if rec else None,
            "answer_accuracy": (sum(1 for r in ans if r["answer_hit"]) / len(ans)) if ans else None,
            "latency_p50": sorted([r["latency_ms"] for r in sub])[len(sub) // 2] if sub else None,
            "latency_p95": sorted([r["latency_ms"] for r in sub])[int(len(sub) * 0.95)] if sub else None,
        }

    payload = {
        "meta": {"top_k": top_k, "queries_file": _relpath(queries_path, ROOT), "total_queries": len(queries)},
        "aggregates": {
            "recall_at_k": recall_at_k,
            "answer_accuracy": answer_accuracy,
            "latency_p50_ms": latency_p50,
            "latency_p95_ms": latency_p95,
        },
        "by_difficulty": by_difficulty,
        "results": results,
    }

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Wrote {out_path}")

    # Summary to stdout
    print("\n--- Summary ---")
    print(f"  Recall@k:     {recall_at_k:.2%}" if recall_at_k is not None else "  Recall@k:     N/A")
    print(f"  Answer acc:   {answer_accuracy:.2%}" if answer_accuracy is not None else "  Answer acc:   N/A")
    print(f"  Latency p50:  {latency_p50} ms" if latency_p50 is not None else "  Latency p50:  N/A")
    print(f"  Latency p95:  {latency_p95} ms" if latency_p95 is not None else "  Latency p95:  N/A")
    for d, stats in by_difficulty.items():
        print(f"  [{d}] n={stats['count']} recall={stats['recall_at_k']} answer={stats['answer_accuracy']} p50={stats['latency_p50']}ms")

    if args.baseline:
        baseline_path = eval_dir / "baseline_metrics.json"
        baseline_payload = {
            "meta": payload["meta"],
            "aggregates": payload["aggregates"],
            "by_difficulty": payload["by_difficulty"],
        }
        with baseline_path.open("w", encoding="utf-8") as f:
            json.dump(baseline_payload, f, indent=2)
        print(f"\nBaseline snapshot written to {baseline_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
