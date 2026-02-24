"""
Re-ingest all PDFs from claw_manuals: clear tenant chunks (and parents/documents),
then run IngestionPipeline.ingest_file() for each PDF under claw_manuals/root/claw_manuals/.

Usage (from project root):
  python scripts/reingest_all.py

Requires: .env with DATABASE_URL, OPENAI_API_KEY, DEFAULT_TENANT_ID.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.config import load_config
from src.db.connection import get_session_factory
from src.db.models import Document, Tenant
from src.ingestion.pipeline import IngestionPipeline
from src.llm.factory import create_embedding_provider
from src.vectorstore.pgvector_store import PostgresVectorStore


def main() -> int:
    tenant_id = os.environ.get("DEFAULT_TENANT_ID", "").strip()
    if not tenant_id:
        print("DEFAULT_TENANT_ID not set in .env", file=sys.stderr)
        return 1

    config = load_config()
    session_factory = get_session_factory()
    session = session_factory()
    try:
        tid = UUID(tenant_id)
        tenant = session.query(Tenant).filter(Tenant.id == tid).first()
        if not tenant:
            print(f"Tenant {tenant_id} not found.", file=sys.stderr)
            return 1
    finally:
        session.close()

    embedder = create_embedding_provider(config.embedding)
    vector_store = PostgresVectorStore(
        tenant_id=tenant_id,
        session_factory=session_factory,
        embedding_model=config.embedding.model,
        embedding_version=1,
    )
    pipeline = IngestionPipeline(
        embedding_provider=embedder,
        vector_store=vector_store,
        chunk_size=config.ingestion.chunk_size,
        chunk_overlap=config.ingestion.chunk_overlap,
        raw_storage_dir=config.ingestion.raw_data_dir,
        child_size_words=getattr(config.ingestion, "child_size_words", 250),
        child_overlap_words=getattr(config.ingestion, "child_overlap_words", 50),
        parent_max_words=getattr(config.ingestion, "parent_max_words", 2000),
        min_chunk_words=getattr(config.ingestion, "min_chunk_words", 15),
    )

    pdf_root = ROOT / "claw_manuals" / "root" / "claw_manuals"
    if not pdf_root.is_dir():
        print(f"PDF root not found: {pdf_root}", file=sys.stderr)
        return 1

    pdf_files = sorted(pdf_root.rglob("*.pdf"))
    if not pdf_files:
        print(f"No PDFs found under {pdf_root}", file=sys.stderr)
        return 1

    # Clear all chunks for tenant (and parents + documents for clean re-ingest)
    sess = session_factory()
    try:
        sess.execute(
            text("DELETE FROM document_chunks WHERE tenant_id = CAST(:tid AS uuid)"),
            {"tid": tenant_id},
        )
        sess.execute(
            text("DELETE FROM document_parents WHERE tenant_id = CAST(:tid AS uuid)"),
            {"tid": tenant_id},
        )
        sess.execute(
            text("DELETE FROM documents WHERE tenant_id = CAST(:tid AS uuid)"),
            {"tid": tenant_id},
        )
        sess.commit()
        print(f"Cleared chunks, parents, and documents for tenant {tenant_id}")
    except Exception as e:
        sess.rollback()
        print(f"Clear failed: {e}", file=sys.stderr)
        return 1
    finally:
        sess.close()

    success = 0
    failed = 0
    total_chunks = 0
    errors: list[str] = []

    for path in pdf_files:
        doc_id = uuid4()
        filename = path.name
        file_type = "pdf"

        sess = session_factory()
        try:
            doc = Document(
                id=doc_id,
                tenant_id=tenant.id,
                filename=filename,
                s3_key=f"reingest:{path.resolve()}",
                file_type=file_type,
                status="pending",
            )
            sess.add(doc)
            sess.commit()
        except Exception as e:
            sess.rollback()
            failed += 1
            errors.append(f"{filename}: document create — {e}")
            continue
        finally:
            sess.close()

        try:
            result = pipeline.ingest_file(path, document_id=str(doc_id))
            if result.status != "success":
                failed += 1
                errors.append(f"{filename}: {result.error_message or result.status}")
                sess = session_factory()
                try:
                    d = sess.query(Document).filter(Document.id == doc_id).first()
                    if d:
                        d.status = "failed"
                        sess.commit()
                finally:
                    sess.close()
                continue
            success += 1
            total_chunks += result.total_chunks
            sess = session_factory()
            try:
                d = sess.query(Document).filter(Document.id == doc_id).first()
                if d:
                    d.status = "completed"
                    d.chunk_count = result.total_chunks
                    d.ingested_at = datetime.now(timezone.utc)
                    d.embedding_model = config.embedding.model
                    d.embedding_version = 1
                    sess.commit()
            finally:
                sess.close()
            print(f"  {filename}: {result.total_chunks} chunks")
        except Exception as e:
            failed += 1
            errors.append(f"{filename}: {e}")
            sess = session_factory()
            try:
                d = sess.query(Document).filter(Document.id == doc_id).first()
                if d:
                    d.status = "failed"
                    sess.commit()
            finally:
                sess.close()

    print()
    print("Summary:")
    print(f"  Files processed: {success + failed}")
    print(f"  Success: {success}")
    print(f"  Failed: {failed}")
    print(f"  Total chunks: {total_chunks}")
    if errors:
        print("  Errors:")
        for err in errors[:20]:
            print(f"    - {err}")
        if len(errors) > 20:
            print(f"    ... and {len(errors) - 20} more")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
