"""
Mock LLM and Embedding providers for local development without API keys.

Activated automatically when OPENAI_API_KEY starts with 'sk-placeholder' or 'sk-mock'.
"""

from __future__ import annotations

import hashlib
import math
import logging
from typing import Any, Iterator

from src.llm.base import BaseLLMProvider, BaseEmbeddingProvider, LLMResponse

logger = logging.getLogger(__name__)

_MOCK_ANSWER = (
    "This is a mock response. Configure a valid OPENAI_API_KEY "
    "to get real answers from your documents."
)


class MockLLMProvider(BaseLLMProvider):
    """Returns a canned answer. Useful for testing the full pipeline without OpenAI costs."""

    def __init__(self, model: str = "mock-llm"):
        self.model = model
        logger.info("MockLLMProvider active — real LLM calls are disabled")

    def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        return LLMResponse(
            content=_MOCK_ANSWER,
            model=self.model,
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        )

    def stream(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> Iterator[str]:
        for word in _MOCK_ANSWER.split():
            yield word + " "


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """Deterministic hash-based embeddings. Same input always returns same vector."""

    def __init__(self, dims: int = 1536):
        self._dims = dims
        logger.info("MockEmbeddingProvider active (dims=%d)", dims)

    def _hash_to_vector(self, text: str) -> list[float]:
        h = hashlib.sha256(text.encode()).hexdigest()
        raw = [int(h[i : i + 2], 16) / 255.0 for i in range(0, min(len(h), self._dims * 2), 2)]
        while len(raw) < self._dims:
            extra = hashlib.sha256((text + str(len(raw))).encode()).hexdigest()
            raw.extend(int(extra[i : i + 2], 16) / 255.0 for i in range(0, min(len(extra), (self._dims - len(raw)) * 2), 2))
        raw = raw[: self._dims]
        norm = math.sqrt(sum(x * x for x in raw)) or 1.0
        return [x / norm for x in raw]

    def embed_text(self, text: str) -> list[float]:
        return self._hash_to_vector(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self._hash_to_vector(t) for t in texts]

    @property
    def dimensions(self) -> int:
        return self._dims


def is_placeholder_key(api_key: str) -> bool:
    """Return True if the API key looks like a placeholder (not a real key)."""
    if not api_key:
        return True
    lower = api_key.lower().strip()
    return lower.startswith("sk-placeholder") or lower.startswith("sk-mock") or lower == "sk-..."
