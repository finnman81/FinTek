"""
Integration tests: admin endpoints (usage, knowledge-gaps, analytics).
"""

from __future__ import annotations

import pytest


class TestAdminUsage:
    def test_usage_returns_stats(self, client, tenant_headers):
        r = client.get("/api/v1/admin/usage", headers=tenant_headers)
        assert r.status_code == 200
        data = r.json()
        assert "total_queries" in data
        assert "total_tokens" in data
        assert "avg_confidence" in data
        assert "low_confidence_queries" in data


class TestAdminKnowledgeGaps:
    def test_knowledge_gaps_returns_list(self, client, tenant_headers):
        r = client.get("/api/v1/admin/knowledge-gaps", headers=tenant_headers)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)


class TestAdminAnalytics:
    def test_analytics_returns_usage_and_gaps(self, client, tenant_headers):
        r = client.get("/api/v1/admin/analytics", headers=tenant_headers)
        assert r.status_code == 200
        data = r.json()
        assert "usage" in data
        assert "knowledge_gaps" in data
        assert "total_queries" in data["usage"]
        assert isinstance(data["knowledge_gaps"], list)
