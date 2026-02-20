"""
Real-DB integration tests for pgvector store.

Requires DATABASE_URL. Skipped when unset. Uses test/sample_docs/ content.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest
from sqlalchemy import text

from src.db.connection import get_session_factory
from src.db.models import Tenant
from src.vectorstore.pgvector_store import PostgresVectorStore


def _require_db():
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not set; skipping real-DB integration test")


@pytest.fixture(scope="module")
def integration_tenant_id():
    """Create a dedicated test tenant for isolation."""
    _require_db()
    session_factory = get_session_factory()
    session = session_factory()
    tenant_id = uuid.uuid4()
    try:
        tenant = Tenant(
            id=tenant_id,
            name="Integration Test Tenant",
            slug=f"test-{tenant_id.hex[:8]}",
        )
        session.add(tenant)
        session.commit()
        yield str(tenant_id)
    finally:
        try:
            session.execute(
                text("DELETE FROM document_chunks WHERE tenant_id = :tid"),
                {"tid": str(tenant_id)},
            )
            session.execute(text("DELETE FROM tenants WHERE id = :tid"), {"tid": str(tenant_id)})
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()


@pytest.mark.integration
class TestPostgresVectorStoreIntegration:
    """Tests that require real Postgres with pgvector."""

    def test_add_and_search_returns_chunk(
        self,
        integration_tenant_id: str,
        sample_docs_path: Path,
    ):
        _require_db()
        session_factory = get_session_factory()
        store = PostgresVectorStore(
            tenant_id=integration_tenant_id,
            session_factory=session_factory,
            embedding_model="text-embedding-3-small",
            embedding_version=1,
        )
        doc_id = str(uuid.uuid4())
        # Use a fixed 1536-dim embedding (pgvector dimension)
        dim = 1536
        embedding = [0.1] * dim
        text_from_sample = "Pump priming procedure. Step 1: Ensure the suction line is filled."
        store.add_documents(
            texts=[text_from_sample],
            embeddings=[embedding],
            metadatas=[{"document_id": doc_id, "chunk_index": 0, "source": "manual_pump_01.txt"}],
        )
        results = store.search(query_embedding=embedding, top_k=5)
        assert len(results) >= 1
        assert any(text_from_sample in r.text for r in results)
        assert store.count() >= 1
