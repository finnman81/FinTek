"""
Real-DB integration tests for ingestion worker (process_one_job).

Requires DATABASE_URL. Skipped when unset. Uses test/sample_docs/ files.
Uses a mock embedder so OPENAI_API_KEY is not required.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import text

from src.db.connection import get_session_factory
from src.db.models import Document, IngestionJob, Tenant
from src.workers.ingestion_worker import process_one_job


def _require_db():
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not set; skipping real-DB integration test")


@pytest.fixture
def integration_tenant_and_document(sample_docs_path: Path):
    """Create a test tenant, document, and ingestion job pointing to a sample file."""
    _require_db()
    session_factory = get_session_factory()
    session = session_factory()
    tenant_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    sample_file = sample_docs_path / "manual_pump_01.txt"
    if not sample_file.exists():
        pytest.skip("test/sample_docs/ not found; run python scripts/generate_sample_docs.py")
    try:
        tenant = Tenant(
            id=tenant_id,
            name="Worker Test Tenant",
            slug=f"worker-test-{tenant_id.hex[:8]}",
        )
        session.add(tenant)
        doc = Document(
            id=doc_id,
            tenant_id=tenant_id,
            filename=sample_file.name,
            s3_key=str(sample_file),
            file_type=".txt",
            status="pending",
        )
        session.add(doc)
        job = IngestionJob(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            document_id=doc_id,
            status="pending",
            metadata_={"file_path": str(sample_file), "filename": sample_file.name},
        )
        session.add(job)
        session.commit()
        yield tenant_id, doc_id, job.id, str(sample_file), sample_file.name
    finally:
        try:
            session.execute(
                text("DELETE FROM ingestion_jobs WHERE tenant_id = :tid"),
                {"tid": str(tenant_id)},
            )
            session.execute(
                text("DELETE FROM document_chunks WHERE tenant_id = :tid"),
                {"tid": str(tenant_id)},
            )
            session.execute(
                text("DELETE FROM documents WHERE tenant_id = :tid"),
                {"tid": str(tenant_id)},
            )
            session.execute(text("DELETE FROM tenants WHERE id = :tid"), {"tid": str(tenant_id)})
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()


@pytest.mark.integration
class TestWorkerIngestionIntegration:
    """Tests that require real Postgres and test/sample_docs/."""

    @patch("src.workers.ingestion_worker.create_embedding_provider")
    def test_process_one_job_completes_and_stores_chunks(
        self,
        mock_create_embedder,
        integration_tenant_and_document,
    ):
        _require_db()
        tenant_id, document_id, job_id, file_path, filename = integration_tenant_and_document
        mock_embedder = MagicMock()
        dim = 1536
        mock_embedder.embed_batch.return_value = [[0.1] * dim]
        mock_embedder.embed_text.return_value = [0.1] * dim
        mock_embedder.dimensions = dim
        mock_create_embedder.return_value = mock_embedder

        chunk_count = process_one_job(
            job_id=job_id,
            tenant_id=tenant_id,
            document_id=document_id,
            file_path=file_path,
            filename=filename,
        )
        assert chunk_count >= 1

        session_factory = get_session_factory()
        session = session_factory()
        try:
            n = session.execute(
                text(
                    "SELECT COUNT(*) FROM document_chunks WHERE document_id = :id AND tenant_id = :tid"
                ),
                {"id": str(document_id), "tid": str(tenant_id)},
            ).scalar()
            assert (n or 0) >= 1
        finally:
            session.close()
