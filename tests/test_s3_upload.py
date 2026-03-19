"""
Unit tests for S3 document upload integration.

Validates: Requirements 6.6 — S3_BUCKET_NAME env var and S3 upload in
the document upload endpoint.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.deps import get_db
from src.db.models import Document, IngestionJob, Tenant

TENANT_ID = "00000000-0000-0000-0000-000000000001"
HEADERS = {"X-Tenant-ID": TENANT_ID}
BUCKET = "industrial-dev-documents-666666666666"
UPLOAD_URL = "/api/v1/documents/upload"


def _mock_session():
    """Build a mock DB session that returns a valid tenant."""
    from sqlalchemy.orm import Session

    session = MagicMock(spec=Session)
    tenant = Tenant(
        id=uuid.UUID(TENANT_ID),
        name="Test Tenant",
        slug="test-tenant",
    )

    def _query(model):
        q = MagicMock()
        if model is Tenant:
            q.filter.return_value.first.return_value = tenant
        else:
            q.filter.return_value.first.return_value = None
            q.filter.return_value.order_by.return_value.first.return_value = None
        return q

    session.query.side_effect = _query
    return session


@pytest.fixture
def s3_client_mock():
    """Patch _get_s3_client to return a mock S3 client."""
    mock_client = MagicMock()
    with patch(
        "src.api.routes.documents._get_s3_client",
        return_value=mock_client,
    ):
        yield mock_client


@pytest.fixture
def s3_env(monkeypatch):
    """Set S3_BUCKET_NAME env var."""
    monkeypatch.setenv("S3_BUCKET_NAME", BUCKET)


@pytest.fixture
def upload_client(s3_client_mock, s3_env):
    """TestClient with mocked DB and S3."""
    session = _mock_session()

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c, session, s3_client_mock
    app.dependency_overrides.clear()


class TestS3Upload:
    """Tests for the POST /documents/upload endpoint with S3."""

    def test_upload_puts_object_to_s3(self, upload_client):
        client, db_session, s3_mock = upload_client
        resp = client.post(
            UPLOAD_URL,
            files={"file": ("report.pdf", b"fake-pdf-content", "application/pdf")},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        s3_mock.put_object.assert_called_once()
        call_kwargs = s3_mock.put_object.call_args.kwargs
        assert call_kwargs["Bucket"] == BUCKET
        assert call_kwargs["Body"] == b"fake-pdf-content"

    def test_upload_s3_key_format(self, upload_client):
        """S3 key follows tenants/{tenant_id}/uploads/{doc_id}/{filename}."""
        client, _, s3_mock = upload_client
        resp = client.post(
            UPLOAD_URL,
            files={"file": ("manual.docx", b"data", "application/octet-stream")},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        key = s3_mock.put_object.call_args.kwargs["Key"]
        parts = key.split("/")
        assert parts[0] == "tenants"
        assert parts[1] == TENANT_ID
        assert parts[2] == "uploads"
        # parts[3] is the doc UUID
        uuid.UUID(parts[3])  # validates it's a UUID
        assert parts[4] == "manual.docx"

    def test_upload_creates_document_record(self, upload_client):
        client, db_session, s3_mock = upload_client
        resp = client.post(
            UPLOAD_URL,
            files={"file": ("test.txt", b"hello", "text/plain")},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        # db.add called twice: Document + IngestionJob
        assert db_session.add.call_count == 2
        doc_arg = db_session.add.call_args_list[0].args[0]
        assert isinstance(doc_arg, Document)
        assert doc_arg.filename == "test.txt"
        assert doc_arg.s3_key.startswith(f"tenants/{TENANT_ID}/uploads/")
        assert doc_arg.status == "pending"

    def test_upload_creates_ingestion_job(self, upload_client):
        client, db_session, _ = upload_client
        resp = client.post(
            UPLOAD_URL,
            files={"file": ("data.csv", b"a,b,c", "text/csv")},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        job_arg = db_session.add.call_args_list[1].args[0]
        assert isinstance(job_arg, IngestionJob)
        assert job_arg.status == "pending"
        assert "s3_key" in job_arg.metadata_

    def test_upload_returns_document_and_job_ids(self, upload_client):
        client, _, _ = upload_client
        resp = client.post(
            UPLOAD_URL,
            files={"file": ("f.pdf", b"bytes", "application/pdf")},
            headers=HEADERS,
        )
        body = resp.json()
        uuid.UUID(body["document_id"])
        uuid.UUID(body["job_id"])

    def test_upload_empty_file_returns_400(self, upload_client):
        client, _, s3_mock = upload_client
        resp = client.post(
            UPLOAD_URL,
            files={"file": ("empty.pdf", b"", "application/pdf")},
            headers=HEADERS,
        )
        assert resp.status_code == 400
        s3_mock.put_object.assert_not_called()

    def test_upload_missing_bucket_env_returns_500(self, s3_client_mock, monkeypatch):
        """When S3_BUCKET_NAME is not set, return 500."""
        monkeypatch.delenv("S3_BUCKET_NAME", raising=False)
        session = _mock_session()

        def override_get_db():
            try:
                yield session
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as client:
            resp = client.post(
                UPLOAD_URL,
                files={"file": ("f.pdf", b"data", "application/pdf")},
                headers=HEADERS,
            )
        app.dependency_overrides.clear()
        assert resp.status_code == 500
        assert "S3_BUCKET_NAME" in resp.json()["detail"]
