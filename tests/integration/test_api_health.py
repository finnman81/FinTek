"""
Integration tests: health endpoints (no auth).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client_no_overrides():
    """Client without dependency overrides for public endpoints."""
    return TestClient(app)


class TestHealth:
    def test_root_health_returns_ok(self, client_no_overrides: TestClient):
        r = client_no_overrides.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "ok"
        assert "version" in data

    def test_api_health_returns_ok(self, client_no_overrides: TestClient):
        r = client_no_overrides.get("/api/v1/health")
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "ok"

    def test_api_health_db_returns_ok_or_503(self, client_no_overrides: TestClient):
        r = client_no_overrides.get("/api/v1/health/db")
        assert r.status_code in (200, 503)
        data = r.json()
        if r.status_code == 200:
            assert data.get("status") == "ok" and data.get("database") == "connected"
        else:
            assert data.get("database") == "disconnected"
