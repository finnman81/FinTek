"""
Unit tests for prompt templates and build_chat_messages.
"""

from __future__ import annotations

import pytest

from src.llm.prompts import (
    SYSTEM_PROMPT,
    NO_CONTEXT_RESPONSE,
    build_chat_messages,
    QUERY_REWRITE_PROMPT,
)


class TestPromptsContent:
    def test_system_prompt_contains_instructions(self):
        assert "context" in SYSTEM_PROMPT.lower()
        assert "cite" in SYSTEM_PROMPT.lower()

    def test_no_context_response_is_non_empty(self):
        assert len(NO_CONTEXT_RESPONSE) > 0
        assert "find" in NO_CONTEXT_RESPONSE.lower() or "relevant" in NO_CONTEXT_RESPONSE.lower()

    def test_query_rewrite_prompt_has_placeholders(self):
        assert "{history}" in QUERY_REWRITE_PROMPT
        assert "{question}" in QUERY_REWRITE_PROMPT


class TestBuildChatMessages:
    def test_returns_list_of_dicts(self):
        messages = build_chat_messages("What is the procedure?", context_chunks=[])
        assert isinstance(messages, list)
        assert all(isinstance(m, dict) and "role" in m and "content" in m for m in messages)

    def test_includes_system_message(self):
        messages = build_chat_messages("Hello?", context_chunks=[])
        roles = [m["role"] for m in messages]
        assert "system" in roles

    def test_includes_user_question(self):
        question = "What is the pump priming step?"
        messages = build_chat_messages(question, context_chunks=[])
        content = " ".join(m.get("content", "") for m in messages)
        assert question in content

    def test_context_appears_in_system_or_user(self):
        chunks = [{"text": "Priming: turn valve A first.", "metadata": {}, "score": 0.9}]
        messages = build_chat_messages("How do I prime?", context_chunks=chunks)
        content = " ".join(m.get("content", "") for m in messages)
        assert "Priming" in content or "valve" in content

    def test_conversation_history_included_when_provided(self):
        history = [
            {"role": "user", "content": "First question"},
            {"role": "assistant", "content": "First answer"},
        ]
        messages = build_chat_messages("Second question?", context_chunks=[], conversation_history=history)
        content = " ".join(m.get("content", "") for m in messages)
        assert "First" in content or "Second" in content
