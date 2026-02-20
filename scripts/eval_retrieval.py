"""
Generic retrieval evaluation script. Works with any tenant and question set.

Run retrieval (embed + vector search) for each question and check whether
any returned source matches the expected substring. Use for regression
testing after tuning chunking or prompts.

Usage:
  python scripts/eval_retrieval.py --tenant-slug claw-demo --questions claw_manuals/eval_questions.json
  python scripts/eval_retrieval.py --tenant <slug-or-UUID> --questions /path/to/questions.json

Question set JSON: array of objects with:
  - question: string
  - expected_source_contains: string (matched case-insensitive against source doc name or chunk text)
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from uuid import UUID

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.orm import Session

from src.core.config import load_config
from src.db.connection import get_session_factory
from src.db.models import Tenant
from src.llm.factory import create_embedding_provider
from src.vectorstore.pgvector_store import PostgresVectorStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_questions(questions_path: Path) -> list[dict]:
    """Load question set JSON. Expects array of { question, expected_source_contains }."""
    if not questions_path.exists():
        raise FileNotFoundError(f"Questions file not found: {questions_path}")
    with open(questions_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "questions" in data:
        return data["questions"]
    raise ValueError("Questions JSON must be an array or object with 'questions' key")


def get_tenant_id(session: Session, tenant_slug_or_uuid: str) -> str:
    """Resolve tenant slug or UUID to tenant ID string."""
    # Try as UUID first
    try:
        u = UUID(tenant_slug_or_uuid)
        tenant = session.query(Tenant).filter(Tenant.id == u).first()
        if tenant:
            return str(tenant.id)
        raise ValueError(f"Tenant not found for UUID: {tenant_slug_or_uuid}")
    except (ValueError, TypeError):
        pass
    tenant = session.query(Tenant).filter(Tenant.slug == tenant_slug_or_uuid).first()
    if not tenant:
        raise ValueError(f"Tenant not found for slug: {tenant_slug_or_uuid}")
    return str(tenant.id)


def run_eval(
    tenant_id: str,
    questions: list[dict],
    top_k: int = 5,
    score_threshold: float = 0.3,
) -> tuple[int, int, list[dict]]:
    """
    Run retrieval for each question and check expected_source_contains.
    Returns (passed, failed, results).
    """
    config = load_config()
    session_factory = get_session_factory()
    embedder = create_embedding_provider(config.embedding)
    vector_store = PostgresVectorStore(
        tenant_id=tenant_id,
        session_factory=session_factory,
        embedding_model=config.embedding.model,
        embedding_version=1,
    )

    passed = 0
    failed = 0
    results = []

    for i, item in enumerate(questions):
        question = item.get("question", "").strip()
        expected = (item.get("expected_source_contains") or item.get("expected_source", "")).strip()
        if not question or not expected:
            logger.warning("Skipping item %d: missing question or expected_source_contains", i + 1)
            failed += 1
            results.append({"question": question, "expected": expected, "passed": False, "reason": "missing fields"})
            continue

        try:
            query_embedding = embedder.embed_text(question)
            search_results = vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
            )
            relevant = [r for r in search_results if r.score >= score_threshold]
        except Exception as e:
            logger.exception("Retrieval failed for: %s", question[:80])
            failed += 1
            results.append({"question": question, "expected": expected, "passed": False, "reason": str(e)})
            continue

        # Check if any source (document name or chunk text) contains expected (case-insensitive).
        # Normalize filenames: treat underscores as spaces so "Fleck 5600" matches "fleck_5600_...".
        pattern = re.compile(re.escape(expected), re.IGNORECASE)
        found = False
        for r in relevant:
            source_name = (r.metadata.get("source") or "").strip()
            source_normalized = source_name.replace("_", " ")
            if pattern.search(source_name) or pattern.search(source_normalized) or pattern.search(r.text):
                found = True
                break

        if found:
            passed += 1
            results.append({"question": question, "expected": expected, "passed": True, "sources": len(relevant)})
        else:
            failed += 1
            sources_preview = [r.metadata.get("source", "?") for r in relevant[:3]]
            results.append({
                "question": question,
                "expected": expected,
                "passed": False,
                "reason": "no matching source",
                "top_sources": sources_preview,
            })

    return passed, failed, results


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate retrieval for a tenant and question set")
    parser.add_argument("--tenant", "--tenant-slug", dest="tenant", type=str, required=True, help="Tenant slug or UUID")
    parser.add_argument("--questions", type=Path, required=True, help="Path to question set JSON")
    parser.add_argument("--top-k", type=int, default=5, help="Retrieval top_k (default: 5)")
    parser.add_argument("--score-threshold", type=float, default=0.3, help="Min score (default: 0.3)")
    parser.add_argument("--verbose", action="store_true", help="Print per-question details")
    args = parser.parse_args()

    questions_path = args.questions if args.questions.is_absolute() else PROJECT_ROOT / args.questions
    questions = load_questions(questions_path)
    logger.info("Loaded %d questions from %s", len(questions), questions_path)

    session_factory = get_session_factory()
    session = session_factory()
    try:
        tenant_id = get_tenant_id(session, args.tenant)
        logger.info("Tenant: %s", tenant_id)
    finally:
        session.close()

    passed, failed, results = run_eval(
        tenant_id=tenant_id,
        questions=questions,
        top_k=args.top_k,
        score_threshold=args.score_threshold,
    )

    total = passed + failed
    pct = (100.0 * passed / total) if total else 0
    print(f"\nEval results: {passed}/{total} passed ({pct:.1f}%)")
    if failed:
        print(f"  Failed: {failed}")
    if args.verbose:
        for i, r in enumerate(results, 1):
            status = "PASS" if r["passed"] else "FAIL"
            print(f"  [{status}] Q{i}: {r['question'][:60]}...")
            if not r["passed"] and r.get("reason"):
                print(f"         Reason: {r['reason']}")
            if not r["passed"] and r.get("top_sources"):
                print(f"         Top sources: {r['top_sources']}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
