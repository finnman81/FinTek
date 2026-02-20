"""
Abstract base classes for LLM and Embedding providers.

All providers must implement these interfaces, enabling model-agnostic
swapping via configuration. Today it's OpenAI; tomorrow it could be
Anthropic, Azure OpenAI, or a local Ollama model.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Iterator


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""
    content: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseLLMProvider(ABC):
    """Abstract interface for LLM text generation."""

    @abstractmethod
    def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a single completion from a list of messages."""
        ...

    @abstractmethod
    def stream(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> Iterator[str]:
        """Stream a completion token-by-token."""
        ...


class BaseEmbeddingProvider(ABC):
    """Abstract interface for text embedding generation."""

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Generate an embedding vector for a single text string."""
        ...

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for a batch of texts."""
        ...

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Return the dimensionality of the embedding vectors."""
        ...
