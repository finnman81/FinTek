"""
Integration tests: auth / tenant requirement and optional Clerk JWT.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest


def _clear_default_tenant_env():
    """Context-manager-style helper: remove default tenant env vars so 401 tests work."""
    return patch.dict(os.environ, {
        "DEFAULT_TENANT_ID": "",
        "DEFAULT_TENANT_SLUG": "",
    })


class TestTenantRequired:
    def test_chat_without_tenant_returns_401(self, client):
        with _clear_default_tenant_env():
            r = client.post("/api/v1/chat", json={"question": "Hello?"})
        assert r.status_code == 401
        assert "X-Tenant-ID" in r.json().get("detail", "") or "tenant" in r.json().get("detail", "").lower()

    def test_documents_list_without_tenant_returns_401(self, client):
        with _clear_default_tenant_env():
            r = client.get("/api/v1/documents")
        assert r.status_code == 401

    def test_upload_without_tenant_returns_401(self, client):
        with _clear_default_tenant_env():
            r = client.post("/api/v1/documents/upload", files={"file": ("x.txt", b"content", "text/plain")})
        assert r.status_code == 401

    def test_admin_usage_without_tenant_returns_401(self, client):
        with _clear_default_tenant_env():
            r = client.get("/api/v1/admin/usage")
        assert r.status_code == 401


class TestWithTenant:
    def test_chat_with_tenant_returns_200(self, client, tenant_headers):
        r = client.post("/api/v1/chat", json={"question": "What is the procedure?"}, headers=tenant_headers)
        assert r.status_code == 200
        data = r.json()
        assert "answer" in data
        assert "sources" in data

    def test_documents_list_with_tenant_returns_200(self, client, tenant_headers):
        r = client.get("/api/v1/documents", headers=tenant_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)


class TestClerkAuth:
    """When Clerk JWT is valid (mocked), /auth/me returns user from token."""

    @patch("src.api.deps.verify_clerk_token")
    def test_me_with_valid_clerk_token_returns_200(self, mock_verify, client, tenant_headers):
        mock_verify.return_value = {"sub": "user_clerk_test", "email": "test@example.com"}
        r = client.get(
            "/api/v1/auth/me",
            headers={**tenant_headers, "Authorization": "Bearer mock-jwt-token"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data.get("tenant_id") == tenant_headers["X-Tenant-ID"]
        assert "user_id" in data

    def test_me_without_tenant_returns_401(self, client):
        with _clear_default_tenant_env():
            r = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer x"})
        assert r.status_code == 401
