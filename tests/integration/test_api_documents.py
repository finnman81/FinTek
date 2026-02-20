"""
Integration tests: document list, upload, status, delete (mocked DB).
"""

from __future__ import annotations

import pytest


class TestListDocuments:
    def test_list_documents_returns_list(self, client, tenant_headers):
        r = client.get("/api/v1/documents", headers=tenant_headers)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)

    def test_list_documents_items_have_expected_fields(self, client_with_document, tenant_headers):
        r = client_with_document.get("/api/v1/documents", headers=tenant_headers)
        assert r.status_code == 200
        data = r.json()
        if data:
            doc = data[0]
            assert "id" in doc
            assert "filename" in doc
            assert "status" in doc
            assert "chunk_count" in doc


class TestUploadDocument:
    def test_upload_returns_document_id_and_job_id(self, client, tenant_headers):
        r = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.txt", b"File content for ingestion.", "text/plain")},
            headers=tenant_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert "document_id" in data
        assert "job_id" in data

    def test_upload_empty_file_returns_400(self, client, tenant_headers):
        r = client.post(
            "/api/v1/documents/upload",
            files={"file": ("empty.txt", b"", "text/plain")},
            headers=tenant_headers,
        )
        assert r.status_code == 400
        assert "empty" in r.json().get("detail", "").lower() or "Empty" in str(r.json())


class TestDocumentStatus:
    def test_status_returns_ok_for_existing_document(self, client_with_document, tenant_headers):
        doc_id = "10000000-0000-0000-0000-000000000001"
        r = client_with_document.get(f"/api/v1/documents/{doc_id}/status", headers=tenant_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["document_id"] == doc_id
        assert "status" in data

    def test_status_invalid_uuid_returns_400(self, client, tenant_headers):
        r = client.get("/api/v1/documents/not-a-uuid/status", headers=tenant_headers)
        assert r.status_code == 400

    def test_status_nonexistent_document_returns_404(self, client, tenant_headers):
        # Use a valid UUID that doesn't exist in mock
        r = client.get(
            "/api/v1/documents/00000000-0000-0000-0000-000000000099/status",
            headers=tenant_headers,
        )
        assert r.status_code == 404


class TestDeleteDocument:
    def test_delete_nonexistent_returns_404(self, client, tenant_headers):
        r = client.delete(
            "/api/v1/documents/00000000-0000-0000-0000-000000000099",
            headers=tenant_headers,
        )
        assert r.status_code == 404

    def test_delete_invalid_uuid_returns_400(self, client, tenant_headers):
        r = client.delete("/api/v1/documents/invalid", headers=tenant_headers)
        assert r.status_code == 400

    def test_delete_existing_returns_200(self, client_with_document, tenant_headers):
        doc_id = "10000000-0000-0000-0000-000000000001"
        r = client_with_document.delete(f"/api/v1/documents/{doc_id}", headers=tenant_headers)
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "deleted"
        assert data.get("document_id") == doc_id
