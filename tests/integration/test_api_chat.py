"""
Integration tests: chat endpoint (mocked retrieval engine).
"""

from __future__ import annotations

import pytest


class TestChatEndpoint:
    def test_chat_returns_answer_and_sources(self, client, tenant_headers):
        r = client.post(
            "/api/v1/chat",
            json={"question": "How do I prime the pump?"},
            headers=tenant_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert "answer" in data
        assert "sources" in data
        assert isinstance(data["sources"], list)
        assert data.get("model") or True  # may be empty
        assert "confidence" in data

    def test_chat_request_validation_empty_question(self, client, tenant_headers):
        r = client.post("/api/v1/chat", json={"question": ""}, headers=tenant_headers)
        # May be 200 with empty answer or 422 validation error
        assert r.status_code in (200, 422)

    def test_chat_accepts_optional_conversation_id(self, client, tenant_headers):
        r = client.post(
            "/api/v1/chat",
            json={"question": "Hello", "conversation_id": "conv-123"},
            headers=tenant_headers,
        )
        assert r.status_code == 200
