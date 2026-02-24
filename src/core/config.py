"""
Centralized configuration loader.

Reads from config/settings.yaml and environment variables.
Environment variables override YAML values.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "settings.yaml"
DATA_DIR = PROJECT_ROOT / "data"


@dataclass
class LLMConfig:
    provider: str = "openai"
    model: str = "gpt-4o"
    temperature: float = 0.1
    max_tokens: int = 2048
    api_key: str = ""


@dataclass
class EmbeddingConfig:
    provider: str = "openai"
    model: str = "text-embedding-3-small"
    dimensions: int = 1536
    api_key: str = ""


@dataclass
class VectorStoreConfig:
    provider: str = "chroma"
    collection_name: str = "documents"
    persist_directory: str = str(DATA_DIR / "processed" / "chroma")
    distance_metric: str = "cosine"


@dataclass
class IngestionConfig:
    chunk_size: int = 1000
    chunk_overlap: int = 200
    child_size_words: int = 250
    child_overlap_words: int = 50
    parent_max_words: int = 2000
    min_chunk_words: int = 20
    supported_extensions: list[str] = field(
        default_factory=lambda: [".pdf", ".docx", ".txt", ".csv", ".md"]
    )
    raw_data_dir: str = str(DATA_DIR / "raw")


@dataclass
class RetrievalConfig:
    use_baseline_path: bool = True
    baseline_top_k: int = 8
    top_k: int = 5
    score_threshold: float = 0.0
    include_metadata: bool = True
    use_hybrid: bool = True
    vector_top_k: int = 40
    lexical_top_k: int = 40
    rrf_k: int = 60
    final_k: int = 14
    ef_search: int = 80
    rerank_top_n: int = 20
    final_context_chunks: int = 5
    use_two_pass_answer: bool = False
    use_reranker: bool = True
    reranker_model: str = ""
    abstain_min_top1_score: float = 0.18
    abstain_min_margin: float = 0.05


@dataclass
class BrandingConfig:
    product_name: str = "Anchorpoint"
    customer_name: str = ""
    customer_logo: str = ""
    accent_color: str = "#2563EB"


@dataclass
class AppConfig:
    app_name: str = "Anchorpoint"
    log_level: str = "INFO"
    query_log_db: str = str(DATA_DIR / "logs" / "queries.db")
    database_url: str = ""  # From DATABASE_URL env; required for production
    branding: BrandingConfig = field(default_factory=BrandingConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    vectorstore: VectorStoreConfig = field(default_factory=VectorStoreConfig)
    ingestion: IngestionConfig = field(default_factory=IngestionConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)


def _deep_update(base: dict, override: dict) -> dict:
    """Recursively merge override dict into base dict."""
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = _deep_update(base[key], value)
        else:
            base[key] = value
    return base


def _apply_env_overrides(raw: dict[str, Any]) -> dict[str, Any]:
    """Override config values with environment variables where set."""
    env_map = {
        "DATABASE_URL": ("database_url",),
        "OPENAI_API_KEY": ("llm", "api_key"),
        "EMBEDDING_API_KEY": ("embedding", "api_key"),
        "LLM_PROVIDER": ("llm", "provider"),
        "LLM_MODEL": ("llm", "model"),
        "EMBEDDING_PROVIDER": ("embedding", "provider"),
        "EMBEDDING_MODEL": ("embedding", "model"),
        "VECTORSTORE_PROVIDER": ("vectorstore", "provider"),
        "LOG_LEVEL": ("log_level",),
    }
    for env_var, path in env_map.items():
        value = os.environ.get(env_var)
        if value is not None:
            if len(path) == 1:
                raw[path[0]] = value
            else:
                current = raw
                for part in path[:-1]:
                    current = current.setdefault(part, {})
                current[path[-1]] = value
    return raw


def load_config(config_path: Path | None = None) -> AppConfig:
    """Load configuration from YAML file with environment variable overrides."""
    path = config_path or CONFIG_PATH
    raw: dict[str, Any] = {}

    if path.exists():
        with open(path, "r") as f:
            raw = yaml.safe_load(f) or {}

    raw = _apply_env_overrides(raw)

    llm_raw = raw.get("llm", {})
    embedding_raw = raw.get("embedding", {})
    vectorstore_raw = raw.get("vectorstore", {})
    ingestion_raw = raw.get("ingestion", {})
    retrieval_raw = raw.get("retrieval", {})

    # If embedding API key not explicitly set, fall back to LLM key
    if not embedding_raw.get("api_key") and llm_raw.get("api_key"):
        embedding_raw["api_key"] = llm_raw["api_key"]

    branding_raw = raw.get("branding", {})

    return AppConfig(
        app_name=raw.get("app_name", "Anchorpoint"),
        log_level=raw.get("log_level", "INFO"),
        query_log_db=raw.get("query_log_db", str(DATA_DIR / "logs" / "queries.db")),
        database_url=raw.get("database_url", os.environ.get("DATABASE_URL", "")),
        branding=BrandingConfig(**{k: v for k, v in branding_raw.items() if k in BrandingConfig.__dataclass_fields__}),
        llm=LLMConfig(**{k: v for k, v in llm_raw.items() if k in LLMConfig.__dataclass_fields__}),
        embedding=EmbeddingConfig(**{k: v for k, v in embedding_raw.items() if k in EmbeddingConfig.__dataclass_fields__}),
        vectorstore=VectorStoreConfig(**{k: v for k, v in vectorstore_raw.items() if k in VectorStoreConfig.__dataclass_fields__}),
        ingestion=IngestionConfig(**{k: v for k, v in ingestion_raw.items() if k in IngestionConfig.__dataclass_fields__}),
        retrieval=RetrievalConfig(**{k: v for k, v in retrieval_raw.items() if k in RetrievalConfig.__dataclass_fields__}),
    )
