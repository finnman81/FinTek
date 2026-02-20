"""
Clear tenant-scoped RAG data (documents + chunks) to avoid duplicates.

Safe by default: runs in dry-run mode unless --yes is provided.
"""

from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

# Ensure project root is on sys.path when running as a script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text

from src.db.connection import get_session_factory
from src.db.models import Tenant


def _scalar(session, sql: str, params: dict) -> int:
    val = session.execute(text(sql), params).scalar()
    return int(val or 0)


def main() -> None:
    parser = argparse.ArgumentParser(description="Clear tenant documents/chunks (avoid duplicates).")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--tenant-slug", type=str, help="Tenant slug (e.g. claw-demo)")
    group.add_argument("--tenant-id", type=str, help="Tenant UUID")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Actually delete data. Without this flag, runs as dry-run.",
    )
    args = parser.parse_args()

    session_factory = get_session_factory()
    session = session_factory()
    try:
        if args.tenant_slug:
            tenant = session.query(Tenant).filter(Tenant.slug == args.tenant_slug).first()
        else:
            tenant_uuid = uuid.UUID(args.tenant_id)
            tenant = session.query(Tenant).filter(Tenant.id == tenant_uuid).first()

        if not tenant:
            raise SystemExit("Tenant not found.")

        tenant_id = tenant.id
        docs = _scalar(session, "SELECT COUNT(*) FROM documents WHERE tenant_id = :tenant_id", {"tenant_id": tenant_id})
        chunks = _scalar(
            session,
            "SELECT COUNT(*) FROM document_chunks WHERE tenant_id = :tenant_id",
            {"tenant_id": tenant_id},
        )
        jobs = _scalar(
            session,
            "SELECT COUNT(*) FROM ingestion_jobs WHERE tenant_id = :tenant_id",
            {"tenant_id": tenant_id},
        )

        print(f"Tenant: {tenant.slug} ({tenant_id})")
        print(f"Would delete: {docs} documents, {chunks} chunks, {jobs} ingestion_jobs")

        if not args.yes:
            print("Dry run only. Re-run with --yes to delete.")
            return

        # Delete in FK-safe order (jobs may reference documents; chunks reference documents)
        session.execute(text("DELETE FROM ingestion_jobs WHERE tenant_id = :tenant_id"), {"tenant_id": tenant_id})
        session.execute(text("DELETE FROM document_chunks WHERE tenant_id = :tenant_id"), {"tenant_id": tenant_id})
        session.execute(text("DELETE FROM document_parents WHERE tenant_id = :tenant_id"), {"tenant_id": tenant_id})
        session.execute(text("DELETE FROM documents WHERE tenant_id = :tenant_id"), {"tenant_id": tenant_id})
        session.commit()

        print("Deleted tenant data successfully.")
    finally:
        session.close()


if __name__ == "__main__":
    main()

