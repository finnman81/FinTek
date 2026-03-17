"""
Pytest configuration and shared fixtures for Munitor AI tests.

Use dependency_overrides for API tests to avoid requiring a real database
or external services (OpenAI, pgvector).
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.main import app
from src.core.config import CONFIG_PATH, load_config
from src.db.models import Tenant, User, Document, IngestionJob
from src.retrieval.engine import RetrievalEngine
from src.vectorstore.base import BaseVectorStore, SearchResult


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def sample_docs_path(project_root: Path) -> Path:
    """Path to test/sample_docs/ (canonical sample set for integration and E2E)."""
    return project_root / "test" / "sample_docs"


@pytest.fixture
def config_path(project_root: Path, tmp_path: Path) -> Path:
    """Optional: use a temporary config file for tests that modify config."""
    return project_root / "config" / "settings.yaml"


@pytest.fixture
def app_config(config_path: Path):
    """Load app config (uses env overrides)."""
    return load_config(config_path)


@pytest.fixture
def env_cleanup():
    """Restore env after tests that mutate os.environ."""
    before = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(before)


# ---------------------------------------------------------------------------
# Mock DB session for API tests (no real DB required)
# ---------------------------------------------------------------------------

def _make_mock_session(
    *,
    tenant: Tenant | None = None,
    documents: list[Document] | None = None,
    document_for_status: Document | None = None,
    job_for_status: IngestionJob | None = None,
) -> MagicMock:
    session = MagicMock(spec=Session)
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.add = MagicMock()
    session.delete = MagicMock()
    session.close = MagicMock()

    tid = tenant.id if tenant else uuid.UUID("00000000-0000-0000-0000-000000000001")
    if tenant is None:
        tenant = Tenant(
            id=tid,
            name="Test Tenant",
            slug="test-tenant",
        )

    def _query(model):
        q = MagicMock()
        # Use "is" to avoid triggering SQLAlchemy __eq__ when model is a SQL expression (e.g. func.count())
        if model is Tenant:
            q.filter.return_value.first.return_value = tenant
        elif model is User:
            q.filter.return_value.first.return_value = None  # use placeholder user
        elif model is Document:
            q.filter.return_value.order_by.return_value.all.return_value = documents or []
            q.filter.return_value.order_by.return_value.first.return_value = None
            q.filter.return_value.first.return_value = document_for_status
        elif model is IngestionJob:
            q.filter.return_value.order_by.return_value.first.return_value = job_for_status
        else:
            # UsageLog aggregates, func.count(...), etc.
            q.filter.return_value.first.return_value = None
            q.filter.return_value.all.return_value = []
            q.filter.return_value.scalar.return_value = 0
            q.filter.return_value.order_by.return_value.all.return_value = []
        return q

    session.query.side_effect = _query
    return session


@pytest.fixture
def mock_db_session() -> MagicMock:
    """Default mock DB session: one tenant, no documents."""
    tenant = Tenant(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        name="Test Tenant",
        slug="test-tenant",
    )
    return _make_mock_session(tenant=tenant, documents=[])


@pytest.fixture
def mock_db_session_with_document() -> MagicMock:
    """Mock DB session with one document and one job for status/delete tests."""
    tid = uuid.UUID("00000000-0000-0000-0000-000000000001")
    doc_id = uuid.UUID("10000000-0000-0000-0000-000000000001")
    job_id = uuid.uuid4()
    tenant = Tenant(id=tid, name="Test", slug="test")
    doc = Document(
        id=doc_id,
        tenant_id=tid,
        filename="test.pdf",
        s3_key="/tmp/test.pdf",
        file_type=".pdf",
        status="completed",
        chunk_count=3,
        created_at=datetime.now(timezone.utc),
    )
    job = IngestionJob(
        id=job_id,
        tenant_id=tid,
        document_id=doc_id,
        status="completed",
    )
    return _make_mock_session(
        tenant=tenant,
        documents=[doc],
        document_for_status=doc,
        job_for_status=job,
    )


# ---------------------------------------------------------------------------
# Mock retrieval engine and vector store
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_vector_store() -> MagicMock:
    store = MagicMock(spec=BaseVectorStore)
    store.search.return_value = [
        SearchResult(
            text="Relevant chunk about pumps.",
            score=0.85,
            metadata={"source": "manual.pdf", "page": 1},
            document_id="chunk-1",
        ),
    ]
    store.count.return_value = 10
    store.add_documents.return_value = ["id1", "id2"]
    store.delete.return_value = None
    store.clear.return_value = None
    return store


@pytest.fixture
def mock_retrieval_engine(mock_vector_store: MagicMock) -> MagicMock:
    from src.llm.base import LLMResponse

    engine = MagicMock(spec=RetrievalEngine)
    engine.query.return_value = type("RetrievalResult", (), {
        "answer": "Based on the manual, the pump should be primed first.",
        "sources": [
            {"document": "manual.pdf", "page": 1, "section": "", "relevance_score": 0.85},
        ],
        "model": "gpt-4o",
        "usage": {"total_tokens": 100, "prompt_tokens": 50, "completion_tokens": 50},
        "confidence": 0.85,
    })()
    return engine


# ---------------------------------------------------------------------------
# FastAPI test client with overrides
# ---------------------------------------------------------------------------

@pytest.fixture
def client(mock_db_session: MagicMock, mock_retrieval_engine: MagicMock) -> Generator[TestClient, None, None]:
    """Test client with mocked get_db and get_retrieval_engine. Requires X-Tenant-ID."""
    from src.api.deps import get_db, get_retrieval_engine

    def override_get_db():
        try:
            yield mock_db_session
        finally:
            pass

    def override_get_retrieval_engine():
        return mock_retrieval_engine

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_retrieval_engine] = override_get_retrieval_engine
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def client_with_document(mock_db_session_with_document: MagicMock, mock_retrieval_engine: MagicMock) -> Generator[TestClient, None, None]:
    """Test client with a pre-existing document (for status/delete tests)."""
    from src.api.deps import get_db, get_retrieval_engine

    def override_get_db():
        try:
            yield mock_db_session_with_document
        finally:
            pass

    def override_get_retrieval_engine():
        return mock_retrieval_engine

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_retrieval_engine] = override_get_retrieval_engine
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Headers used by protected endpoints
# ---------------------------------------------------------------------------

@pytest.fixture
def tenant_headers() -> dict[str, str]:
    return {"X-Tenant-ID": "00000000-0000-0000-0000-000000000001"}
