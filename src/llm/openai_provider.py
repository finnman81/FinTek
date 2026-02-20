"""
OpenAI implementations of LLM and Embedding providers.
"""

from __future__ import annotations

import logging
from typing import Any, Iterator

from openai import OpenAI

from src.llm.base import BaseLLMProvider, BaseEmbeddingProvider, LLMResponse

logger = logging.getLogger(__name__)


class OpenAILLMProvider(BaseLLMProvider):
    """OpenAI chat completion provider (GPT-4o, GPT-4o-mini, etc.)."""

    def __init__(self, api_key: str, model: str = "gpt-4o", temperature: float = 0.1, max_tokens: int = 2048):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.default_temperature = temperature
        self.default_max_tokens = max_tokens

    def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature or self.default_temperature,
            max_tokens=max_tokens or self.default_max_tokens,
            **kwargs,
        )

        choice = response.choices[0]
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }

        logger.info(f"OpenAI completion: {usage['total_tokens']} tokens used")

        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            usage=usage,
        )

    def stream(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> Iterator[str]:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature or self.default_temperature,
            max_tokens=max_tokens or self.default_max_tokens,
            stream=True,
            **kwargs,
        )

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI embedding provider (text-embedding-3-small, etc.)."""

    def __init__(self, api_key: str, model: str = "text-embedding-3-small", dims: int = 1536):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self._dimensions = dims

    def embed_text(self, text: str) -> list[float]:
        response = self.client.embeddings.create(
            model=self.model,
            input=text,
        )
        return response.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        # OpenAI supports batch embedding natively
        response = self.client.embeddings.create(
            model=self.model,
            input=texts,
        )

        # Sort by index to maintain order
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return [item.embedding for item in sorted_data]

    @property
    def dimensions(self) -> int:
        return self._dimensions
