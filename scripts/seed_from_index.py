"""
Generic seed script: populate RAG knowledge base from an index JSON.

Works with any data source (e.g. claw_manuals for testing, customer manuals for production).
Switch sources via environment variables or CLI; no code changes needed.

Environment variables:
  SEED_INDEX_PATH   Path to index JSON (array of objects with "relative_path").
  SEED_BASE_PATH   Base directory where files live; paths are base_path + relative_path.
  SEED_TENANT_SLUG Tenant slug to use (created if missing).
  SEED_TENANT_NAME Display name for tenant when creating (default: derived from slug).

Usage:
  # From claw_manuals (testing)
  SEED_INDEX_PATH=claw_manuals/root/claw_manuals/manual_index.json \\
  SEED_BASE_PATH=claw_manuals/root/claw_manuals \\
  SEED_TENANT_SLUG=claw-demo \\
  python scripts/seed_from_index.py

  # From customer data
  SEED_INDEX_PATH=/path/to/customer/index.json \\
  SEED_BASE_PATH=/path/to/customer/manuals/ \\
  SEED_TENANT_SLUG=acme-corp \\
  python scripts/seed_from_index.py

  # Options: --dry-run, --limit N, --index-path, --base-path, --tenant-slug, --tenant-name
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

# Project root (parent of scripts/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.orm import Session

from src.core.config import load_config
from src.db.connection import get_session_factory
from src.db.models import Document, Tenant
from src.ingestion.pipeline import IngestionPipeline
from src.llm.factory import create_embedding_provider
from src.vectorstore.pgvector_store import PostgresVectorStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_index(index_path: Path) -> list[dict]:
    """Load index JSON. Expects array of objects with at least 'relative_path'."""
    if not index_path.exists():
        raise FileNotFoundError(f"Index file not found: {index_path}")
    with open(index_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # Allow { "documents": [...] } or similar
        for key in ("documents", "entries", "manuals", "items"):
            if key in data and isinstance(data[key], list):
                return data[key]
        raise ValueError("Index JSON must be an array or dict with a list value (e.g. 'documents')")
    raise ValueError("Index JSON must be an array or object")


def resolve_file_paths(
    index_entries: list[dict],
    base_path: Path,
    supported_extensions: tuple[str, ...] = (".pdf", ".docx", ".txt", ".csv", ".md"),
) -> list[tuple[Path, dict]]:
    """Return list of (absolute_path, entry) for existing files."""
    resolved: list[tuple[Path, dict]] = []
    for entry in index_entries:
        rel = entry.get("relative_path") or entry.get("path")
        if not rel:
            logger.warning("Index entry missing relative_path, skipping: %s", entry.get("id", entry))
            continue
        full = (base_path / rel).resolve()
        if not full.exists():
            logger.debug("File not found, skipping: %s", full)
            continue
        if full.suffix.lower() not in supported_extensions:
            logger.debug("Unsupported extension, skipping: %s", full)
            continue
        resolved.append((full, entry))
    return resolved


def get_or_create_tenant(
    session: Session,
    slug: str,
    name: str | None = None,
) -> Tenant:
    """Get tenant by slug, or create with given name."""
    tenant = session.query(Tenant).filter(Tenant.slug == slug).first()
    if tenant:
        return tenant
    display_name = name or slug.replace("-", " ").replace("_", " ").title()
    tenant = Tenant(name=display_name, slug=slug)
    session.add(tenant)
    session.commit()
    session.refresh(tenant)
    logger.info("Created tenant: %s (%s)", display_name, tenant.id)
    return tenant


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed RAG knowledge base from an index JSON (modular: works for test or customer data)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only list files that would be ingested, do not run pipeline",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        metavar="N",
        help="Ingest at most N files (0 = no limit)",
    )
    parser.add_argument(
        "--index-path",
        type=Path,
        default=None,
        help="Path to index JSON (overrides SEED_INDEX_PATH)",
    )
    parser.add_argument(
        "--base-path",
        type=Path,
        default=None,
        help="Base directory for files (overrides SEED_BASE_PATH)",
    )
    parser.add_argument(
        "--tenant-slug",
        type=str,
        default=None,
        help="Tenant slug (overrides SEED_TENANT_SLUG)",
    )
    parser.add_argument(
        "--tenant-name",
        type=str,
        default=None,
        help="Tenant display name when creating (overrides SEED_TENANT_NAME)",
    )
    args = parser.parse_args()

    index_path = args.index_path or Path(os.environ.get("SEED_INDEX_PATH", ""))
    base_path = args.base_path or Path(os.environ.get("SEED_BASE_PATH", ""))
    tenant_slug = args.tenant_slug or os.environ.get("SEED_TENANT_SLUG", "claw-demo")
    tenant_name = args.tenant_name or os.environ.get("SEED_TENANT_NAME", "")

    if not index_path or not str(index_path).strip():
        logger.error("Set SEED_INDEX_PATH or pass --index-path")
        sys.exit(1)
    if not base_path or not str(base_path).strip():
        logger.error("Set SEED_BASE_PATH or pass --base-path")
        sys.exit(1)

    index_path = index_path if index_path.is_absolute() else PROJECT_ROOT / index_path
    base_path = base_path if base_path.is_absolute() else PROJECT_ROOT / base_path

    index_entries = load_index(index_path)
    logger.info("Loaded %d entries from index", len(index_entries))

    supported = (".pdf", ".docx", ".txt", ".csv", ".md")
    resolved = resolve_file_paths(index_entries, base_path, supported)
    logger.info("Resolved %d existing files to ingest", len(resolved))

    if not resolved:
        logger.warning("No files to ingest. Check SEED_BASE_PATH and that files exist.")
        sys.exit(0)

    if args.limit:
        resolved = resolved[: args.limit]
        logger.info("Limited to first %d files", len(resolved))

    if args.dry_run:
        for path, entry in resolved:
            title = entry.get("title") or entry.get("file_name") or path.name
            logger.info("Would ingest: %s (%s)", path, title)
        logger.info("Dry run complete. %d files would be ingested.", len(resolved))
        return

    config = load_config()
    session_factory = get_session_factory()
    embedder = create_embedding_provider(config.embedding)
    vector_store = PostgresVectorStore(
        tenant_id="",  # set per-tenant below
        session_factory=session_factory,
        embedding_model=config.embedding.model,
        embedding_version=1,
    )
    pipeline = IngestionPipeline(
        embedding_provider=embedder,
        vector_store=vector_store,
        chunk_size=config.ingestion.chunk_size,
        chunk_overlap=config.ingestion.chunk_overlap,
        child_size_words=getattr(config.ingestion, "child_size_words", 250),
        child_overlap_words=getattr(config.ingestion, "child_overlap_words", 50),
        parent_max_words=getattr(config.ingestion, "parent_max_words", 2000),
        min_chunk_words=getattr(config.ingestion, "min_chunk_words", 15),
    )

    session = session_factory()
    try:
        tenant = get_or_create_tenant(session, tenant_slug, tenant_name or None)
        tenant_id_str = str(tenant.id)
        vector_store.tenant_id = tenant_id_str
    finally:
        session.close()

    success = 0
    failed = 0
    total_chunks = 0

    for path, entry in resolved:
        doc_id = uuid4()
        filename = entry.get("file_name") or path.name
        file_type = (path.suffix or "").lstrip(".").lower() or "pdf"

        session = session_factory()
        try:
            doc = Document(
                id=doc_id,
                tenant_id=tenant.id,
                filename=filename,
                s3_key=f"seed:{path.resolve()}",
                file_type=file_type,
                status="pending",
            )
            session.add(doc)
            session.commit()
        except Exception as e:
            logger.exception("Failed to create document record for %s: %s", path.name, e)
            session.rollback()
            failed += 1
            continue
        finally:
            session.close()

        try:
            result = pipeline.ingest_file(path, document_id=str(doc_id))
            if result.status != "success":
                logger.warning("Ingestion failed for %s: %s", path.name, result.error_message)
                failed += 1
                session = session_factory()
                try:
                    doc = session.query(Document).filter(Document.id == doc_id).first()
                    if doc:
                        doc.status = "failed"
                        session.commit()
                finally:
                    session.close()
                continue
            success += 1
            total_chunks += result.total_chunks
            session = session_factory()
            try:
                doc = session.query(Document).filter(Document.id == doc_id).first()
                if doc:
                    doc.status = "completed"
                    doc.chunk_count = result.total_chunks
                    doc.ingested_at = datetime.now(timezone.utc)
                    doc.embedding_model = config.embedding.model
                    doc.embedding_version = 1
                    session.commit()
            finally:
                session.close()
            logger.info("Ingested %s: %d chunks", filename, result.total_chunks)
        except Exception as e:
            logger.exception("Ingestion error for %s: %s", path.name, e)
            failed += 1
            session = session_factory()
            try:
                doc = session.query(Document).filter(Document.id == doc_id).first()
                if doc:
                    doc.status = "failed"
                    session.commit()
            finally:
                session.close()

    logger.info(
        "Seed complete. Success: %d, Failed: %d, Total chunks: %d. Tenant: %s (%s)",
        success,
        failed,
        total_chunks,
        tenant_slug,
        tenant_id_str,
    )
    if success:
        print(f"\nTo use this tenant in the web app, set:\n  NEXT_PUBLIC_DEFAULT_TENANT_ID={tenant_id_str}\n", file=sys.stderr)


if __name__ == "__main__":
    main()
