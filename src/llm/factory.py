"""
Factory functions for creating LLM and Embedding providers from configuration.

This is the single point where provider selection happens. Adding a new provider
means: (1) implement the base class, (2) add an entry here.
"""

from __future__ import annotations

from src.core.config import LLMConfig, EmbeddingConfig
from src.llm.base import BaseLLMProvider, BaseEmbeddingProvider
from src.llm.openai_provider import OpenAILLMProvider, OpenAIEmbeddingProvider
from src.llm.mock_provider import MockLLMProvider, MockEmbeddingProvider, is_placeholder_key


def create_llm_provider(config: LLMConfig) -> BaseLLMProvider:
    """Create an LLM provider based on configuration."""
    if is_placeholder_key(config.api_key):
        return MockLLMProvider(model=f"mock-{config.model}")

    providers = {
        "openai": lambda: OpenAILLMProvider(
            api_key=config.api_key,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        ),
    }

    factory = providers.get(config.provider)
    if factory is None:
        supported = ", ".join(providers.keys())
        raise ValueError(f"Unknown LLM provider '{config.provider}'. Supported: {supported}")

    return factory()


def create_embedding_provider(config: EmbeddingConfig) -> BaseEmbeddingProvider:
    """Create an embedding provider based on configuration."""
    if is_placeholder_key(config.api_key):
        return MockEmbeddingProvider(dims=config.dimensions)

    providers = {
        "openai": lambda: OpenAIEmbeddingProvider(
            api_key=config.api_key,
            model=config.model,
            dims=config.dimensions,
        ),
    }

    factory = providers.get(config.provider)
    if factory is None:
        supported = ", ".join(providers.keys())
        raise ValueError(f"Unknown embedding provider '{config.provider}'. Supported: {supported}")

    return factory()
