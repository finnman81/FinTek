"""
RAG retrieval tuning script.

Tests combinations of top_k and score_threshold against a question set,
reports pass-rate for each combo, and prints the best configuration.

Chunking params (chunk_size, chunk_overlap) require re-ingestion and are
tested separately with --rechunk mode.

Usage:
  # Test retrieval params only (fast — no re-ingestion):
  python scripts/tune_retrieval.py \
    --tenant-slug claw-demo \
    --questions claw_manuals/eval_questions_50.json

  # Test chunking + retrieval (slow — re-ingests for each chunk config):
  python scripts/tune_retrieval.py \
    --tenant-slug claw-demo \
    --questions claw_manuals/eval_questions_50.json \
    --rechunk \
    --index-path claw_manuals/root/claw_manuals/manual_index.json \
    --base-path claw_manuals/root/claw_manuals
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from pathlib import Path
from uuid import UUID

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text as sa_text
from sqlalchemy.orm import Session

from src.core.config import load_config
from src.db.connection import get_session_factory
from src.db.models import Tenant
from src.llm.factory import create_embedding_provider
from src.vectorstore.pgvector_store import PostgresVectorStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_questions(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else data.get("questions", [])


def get_tenant_id(session: Session, slug_or_uuid: str) -> str:
    try:
        u = UUID(slug_or_uuid)
        t = session.query(Tenant).filter(Tenant.id == u).first()
        if t:
            return str(t.id)
    except (ValueError, TypeError):
        pass
    t = session.query(Tenant).filter(Tenant.slug == slug_or_uuid).first()
    if not t:
        raise SystemExit(f"Tenant not found: {slug_or_uuid}")
    return str(t.id)


def embed_questions(questions: list[dict], embedder) -> list[list[float]]:
    """Embed all questions up front so we only call the API once per question."""
    embeddings = []
    for i, q in enumerate(questions):
        emb = embedder.embed_text(q["question"])
        embeddings.append(emb)
        if (i + 1) % 10 == 0:
            logger.info("Embedded %d/%d questions", i + 1, len(questions))
    logger.info("Embedded all %d questions", len(questions))
    return embeddings


def eval_retrieval_cached(
    tenant_id: str,
    questions: list[dict],
    question_embeddings: list[list[float]],
    session_factory,
    embedding_model: str,
    top_k: int,
    score_threshold: float,
) -> tuple[int, int, list[dict]]:
    """Run retrieval eval with pre-computed embeddings; return (passed, failed, details)."""
    max_top_k = top_k
    vs = PostgresVectorStore(
        tenant_id=tenant_id,
        session_factory=session_factory,
        embedding_model=embedding_model,
        embedding_version=1,
    )
    passed = failed = 0
    details: list[dict] = []

    for q, emb in zip(questions, question_embeddings):
        question = q["question"]
        expected = q.get("expected_source_contains", "")
        if not expected:
            continue

        results = vs.search(query_embedding=emb, top_k=max_top_k)
        relevant = [r for r in results if r.score >= score_threshold]

        pattern = re.compile(re.escape(expected), re.IGNORECASE)
        found = False
        for r in relevant:
            source = (r.metadata.get("source") or "").replace("_", " ")
            if pattern.search(source) or pattern.search(r.text):
                found = True
                break

        if found:
            passed += 1
        else:
            failed += 1
        details.append({"q": question[:60], "expected": expected, "pass": found, "n_results": len(relevant)})

    return passed, failed, details


def eval_retrieval_hybrid_cached(
    tenant_id: str,
    questions: list[dict],
    question_embeddings: list[list[float]],
    session_factory,
    embedding_model: str,
    vector_top_k: int = 40,
    lexical_top_k: int = 40,
    rrf_k: int = 60,
    final_k: int = 20,
    ef_search: int = 80,
    score_threshold: float = 0.0,
) -> tuple[int, int, list[dict], float]:
    """Run hybrid (dense + lexical + RRF) retrieval eval; return (passed, failed, details, latency_sec)."""
    import time as _time
    vs = PostgresVectorStore(
        tenant_id=tenant_id,
        session_factory=session_factory,
        embedding_model=embedding_model,
        embedding_version=1,
    )
    passed = failed = 0
    details: list[dict] = []
    t0 = _time.perf_counter()
    for q, emb in zip(questions, question_embeddings):
        question = q["question"]
        expected = q.get("expected_source_contains", "")
        if not expected:
            continue
        try:
            results = vs.search_hybrid(
                query_text=question,
                query_embedding=emb,
                vector_top_k=vector_top_k,
                lexical_top_k=lexical_top_k,
                rrf_k=rrf_k,
                final_k=final_k,
                ef_search=ef_search,
            )
        except Exception as e:
            logger.warning("Hybrid search failed for %s: %s", question[:40], e)
            results = []
        relevant = [r for r in results if r.score >= score_threshold]
        pattern = re.compile(re.escape(expected), re.IGNORECASE)
        found = False
        for r in relevant:
            source = (r.metadata.get("source") or "").replace("_", " ")
            if pattern.search(source) or pattern.search(r.text):
                found = True
                break
        if found:
            passed += 1
        else:
            failed += 1
        details.append({"q": question[:60], "expected": expected, "pass": found, "n_results": len(relevant)})
    latency = _time.perf_counter() - t0
    return passed, failed, details, latency


# ---------------------------------------------------------------------------
# Re-chunk + re-ingest
# ---------------------------------------------------------------------------

def reingest(
    tenant_id: str,
    session_factory,
    index_path: Path,
    base_path: Path,
    chunk_size: int,
    chunk_overlap: int,
    embedding_model: str,
):
    """Clear tenant data and re-ingest with given chunking params."""
    from src.ingestion.pipeline import IngestionPipeline
    from src.db.models import Document
    from uuid import uuid4
    from datetime import datetime, timezone

    config = load_config()
    embedder = create_embedding_provider(config.embedding)
    vs = PostgresVectorStore(tenant_id=tenant_id, session_factory=session_factory, embedding_model=embedding_model)
    pipeline = IngestionPipeline(embedding_provider=embedder, vector_store=vs, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    # Clear existing data for this tenant (chunks first, then parents, then documents)
    session = session_factory()
    try:
        session.execute(sa_text("DELETE FROM document_chunks WHERE tenant_id = CAST(:tid AS uuid)"), {"tid": tenant_id})
        session.execute(sa_text("DELETE FROM document_parents WHERE tenant_id = CAST(:tid AS uuid)"), {"tid": tenant_id})
        session.execute(sa_text("DELETE FROM documents WHERE tenant_id = CAST(:tid AS uuid)"), {"tid": tenant_id})
        session.commit()
    finally:
        session.close()

    # Load index and re-ingest
    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)

    supported = (".pdf", ".docx", ".txt", ".csv", ".md")
    total_chunks = 0
    for entry in index:
        rel = entry.get("relative_path") or entry.get("path")
        if not rel:
            continue
        full = (base_path / rel).resolve()
        if not full.exists() or full.suffix.lower() not in supported:
            continue

        doc_id = uuid4()
        session = session_factory()
        try:
            doc = Document(
                id=doc_id,
                tenant_id=UUID(tenant_id),
                filename=entry.get("file_name") or full.name,
                s3_key=f"tune:{full}",
                file_type=full.suffix.lstrip(".").lower(),
                status="pending",
            )
            session.add(doc)
            session.commit()
        except Exception:
            session.rollback()
            continue
        finally:
            session.close()

        try:
            result = pipeline.ingest_file(full, document_id=str(doc_id))
            if result.status == "success":
                total_chunks += result.total_chunks
                session = session_factory()
                try:
                    doc = session.query(Document).filter(Document.id == doc_id).first()
                    if doc:
                        doc.status = "completed"
                        doc.chunk_count = result.total_chunks
                        doc.ingested_at = datetime.now(timezone.utc)
                        session.commit()
                finally:
                    session.close()
        except Exception:
            pass

    return total_chunks


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Tune RAG retrieval parameters")
    parser.add_argument("--tenant-slug", "--tenant", dest="tenant", required=True)
    parser.add_argument("--questions", type=Path, required=True)
    parser.add_argument("--rechunk", action="store_true", help="Also test chunking params (requires --index-path and --base-path; slow)")
    parser.add_argument("--hybrid", action="store_true", help="Test hybrid (dense+lexical+RRF) params instead of dense-only")
    parser.add_argument("--index-path", type=Path, default=None)
    parser.add_argument("--base-path", type=Path, default=None)
    args = parser.parse_args()

    questions_path = args.questions if args.questions.is_absolute() else PROJECT_ROOT / args.questions
    questions = load_questions(questions_path)
    total_q = len(questions)

    config = load_config()
    session_factory = get_session_factory()
    embedder = create_embedding_provider(config.embedding)

    session = session_factory()
    try:
        tenant_id = get_tenant_id(session, args.tenant)
    finally:
        session.close()

    print(f"Tenant: {args.tenant} ({tenant_id})")
    print(f"Questions: {total_q}")
    print()

    # Parameter grid
    top_k_values = [5, 8, 10, 12, 15]
    threshold_values = [0.15, 0.20, 0.25, 0.30, 0.35]
    chunk_configs = [(800, 150), (1000, 200), (1200, 250), (1500, 300)] if args.rechunk else []
    # Hybrid sweep (small grid)
    vector_top_k_vals = [20, 40, 80] if args.hybrid else [40]
    lexical_top_k_vals = [20, 40] if args.hybrid else [40]
    rrf_k_vals = [60, 120] if args.hybrid else [60]
    ef_search_vals = [40, 80, 120] if args.hybrid else [80]

    # Pre-compute embeddings (50 API calls, done once regardless of param combos)
    print("Embedding questions...")
    question_embeddings = embed_questions(questions, embedder)
    print()

    results_table: list[dict] = []

    if args.hybrid:
        print("--- Hybrid retrieval sweep ---")
        for vtk in vector_top_k_vals:
            for ltk in lexical_top_k_vals:
                for rrf in rrf_k_vals:
                    for ef in ef_search_vals:
                        p, f, details, lat = eval_retrieval_hybrid_cached(
                            tenant_id, questions, question_embeddings, session_factory,
                            config.embedding.model,
                            vector_top_k=vtk, lexical_top_k=ltk, rrf_k=rrf, final_k=20, ef_search=ef,
                        )
                        total_eval = p + f
                        pct = 100 * p / total_eval if total_eval else 0
                        results_table.append({
                            "vector_top_k": vtk, "lexical_top_k": ltk, "rrf_k": rrf, "ef_search": ef,
                            "passed": p, "total": total_eval, "pct": pct, "latency_sec": round(lat, 2),
                        })
                        print(f"  vector_top_k={vtk} lexical_top_k={ltk} rrf_k={rrf} ef_search={ef} => {p}/{total_eval} ({pct:.1f}%) {lat:.1f}s")
    elif args.rechunk:
        if not args.index_path or not args.base_path:
            raise SystemExit("--rechunk requires --index-path and --base-path")
        index_path = args.index_path if args.index_path.is_absolute() else PROJECT_ROOT / args.index_path
        base_path = args.base_path if args.base_path.is_absolute() else PROJECT_ROOT / args.base_path

        for cs, co in chunk_configs:
            print(f"--- Re-ingesting: chunk_size={cs}, chunk_overlap={co} ---")
            t0 = time.time()
            n_chunks = reingest(tenant_id, session_factory, index_path, base_path, cs, co, config.embedding.model)
            ingest_time = time.time() - t0
            print(f"    Chunks: {n_chunks} ({ingest_time:.0f}s)")

            # Re-embed questions for the new chunk set (embeddings are question-side, so reuse)
            for top_k in top_k_values:
                for threshold in threshold_values:
                    p, f, _ = eval_retrieval_cached(tenant_id, questions, question_embeddings, session_factory, config.embedding.model, top_k, threshold)
                    pct = 100 * p / total_q if total_q else 0
                    results_table.append({"chunk_size": cs, "chunk_overlap": co, "top_k": top_k, "threshold": threshold, "passed": p, "total": total_q, "pct": pct})
    else:
        for top_k in top_k_values:
            for threshold in threshold_values:
                p, f, details = eval_retrieval_cached(tenant_id, questions, question_embeddings, session_factory, config.embedding.model, top_k, threshold)
                pct = 100 * p / total_q if total_q else 0
                results_table.append({"top_k": top_k, "threshold": threshold, "passed": p, "total": total_q, "pct": pct})
                print(f"  top_k={top_k:2d}  threshold={threshold:.2f}  => {p}/{total_q} ({pct:.1f}%)")

    # Sort by pass rate desc, then latency asc for hybrid
    if results_table and "vector_top_k" in results_table[0]:
        results_table.sort(key=lambda r: (-r["pct"], r.get("latency_sec", 0)))
    else:
        results_table.sort(key=lambda r: (-r["pct"], r["top_k"], -r["threshold"]))

    print()
    print("=" * 60)
    print("TOP 5 CONFIGURATIONS")
    print("=" * 60)
    for i, r in enumerate(results_table[:5], 1):
        if "vector_top_k" in r:
            print(f"  {i}. vector_top_k={r['vector_top_k']} lexical_top_k={r['lexical_top_k']} rrf_k={r['rrf_k']} ef_search={r['ef_search']} => {r['passed']}/{r['total']} ({r['pct']:.1f}%) {r.get('latency_sec', 0)}s")
        else:
            cs_str = f"chunk_size={r['chunk_size']}, chunk_overlap={r['chunk_overlap']}, " if "chunk_size" in r else ""
            print(f"  {i}. {cs_str}top_k={r['top_k']}, threshold={r['threshold']:.2f} => {r['passed']}/{r['total']} ({r['pct']:.1f}%)")

    best = results_table[0]
    print()
    print("RECOMMENDED settings.yaml changes:")
    if "chunk_size" in best:
        print(f"  ingestion.chunk_size: {best['chunk_size']}")
        print(f"  ingestion.chunk_overlap: {best['chunk_overlap']}")
    if "vector_top_k" in best:
        print(f"  retrieval.use_hybrid: true")
        print(f"  retrieval.vector_top_k: {best['vector_top_k']}")
        print(f"  retrieval.lexical_top_k: {best['lexical_top_k']}")
        print(f"  retrieval.rrf_k: {best['rrf_k']}")
        print(f"  retrieval.ef_search: {best['ef_search']}")
    else:
        print(f"  retrieval.top_k: {best['top_k']}")
        print(f"  retrieval.score_threshold: {best['threshold']}")

    # Show failures for the best config (verbose)
    if "vector_top_k" in best:
        _, _, details, _ = eval_retrieval_hybrid_cached(
            tenant_id, questions, question_embeddings, session_factory, config.embedding.model,
            vector_top_k=best["vector_top_k"], lexical_top_k=best["lexical_top_k"],
            rrf_k=best["rrf_k"], ef_search=best["ef_search"],
        )
    else:
        _, _, details = eval_retrieval_cached(tenant_id, questions, question_embeddings, session_factory, config.embedding.model, best["top_k"], best["threshold"])
    failures = [d for d in details if not d["pass"]]
    if failures:
        print()
        print(f"FAILURES with best config ({len(failures)}):")
        for d in failures:
            print(f"  - {d['q']}...  (expected: {d['expected']}, results returned: {d['n_results']})")


if __name__ == "__main__":
    main()
