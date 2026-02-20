"""
Unit tests for configuration loading (config/settings.yaml and env overrides).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from src.core.config import (
    CONFIG_PATH,
    PROJECT_ROOT,
    DATA_DIR,
    AppConfig,
    LLMConfig,
    EmbeddingConfig,
    VectorStoreConfig,
    IngestionConfig,
    RetrievalConfig,
    BrandingConfig,
    load_config,
    _apply_env_overrides,
    _deep_update,
)


class TestConfigPaths:
    def test_project_root_is_directory(self):
        assert PROJECT_ROOT.is_dir()
        assert (PROJECT_ROOT / "src").is_dir()

    def test_config_path_exists(self):
        assert CONFIG_PATH.exists()
        assert CONFIG_PATH.suffix == ".yaml"

    def test_data_dir_under_project_root(self):
        assert DATA_DIR == PROJECT_ROOT / "data"


class TestDeepUpdate:
    def test_shallow_override(self):
        base = {"a": 1, "b": 2}
        override = {"b": 20}
        _deep_update(base, override)
        assert base == {"a": 1, "b": 20}

    def test_nested_override(self):
        base = {"a": {"x": 1, "y": 2}, "b": 3}
        override = {"a": {"y": 20}}
        _deep_update(base, override)
        assert base == {"a": {"x": 1, "y": 20}, "b": 3}


class TestApplyEnvOverrides:
    def test_single_key_override(self, env_cleanup):
        os.environ["LOG_LEVEL"] = "DEBUG"
        raw = {"log_level": "INFO"}
        _apply_env_overrides(raw)
        assert raw["log_level"] == "DEBUG"

    def test_nested_key_override(self, env_cleanup):
        os.environ["LLM_MODEL"] = "gpt-4o-mini"
        raw = {"llm": {"model": "gpt-4o"}}
        _apply_env_overrides(raw)
        assert raw["llm"]["model"] == "gpt-4o-mini"

    def test_database_url_single_key(self, env_cleanup):
        os.environ["DATABASE_URL"] = "postgresql://localhost/test"
        raw = {}
        _apply_env_overrides(raw)
        assert raw["database_url"] == "postgresql://localhost/test"

    def test_unset_env_does_not_override(self, env_cleanup):
        if "LLM_MODEL" in os.environ:
            del os.environ["LLM_MODEL"]
        raw = {"llm": {"model": "gpt-4o"}}
        _apply_env_overrides(raw)
        assert raw["llm"]["model"] == "gpt-4o"


class TestLoadConfig:
    def test_load_config_returns_app_config(self, app_config: AppConfig):
        assert isinstance(app_config, AppConfig)
        assert app_config.app_name in ("Anchorpoint",)

    def test_llm_config_defaults(self, app_config: AppConfig):
        assert isinstance(app_config.llm, LLMConfig)
        assert app_config.llm.model
        assert app_config.llm.temperature >= 0
        assert app_config.llm.max_tokens > 0

    def test_embedding_config_defaults(self, app_config: AppConfig):
        assert isinstance(app_config.embedding, EmbeddingConfig)
        assert app_config.embedding.dimensions == 1536

    def test_vectorstore_config(self, app_config: AppConfig):
        assert isinstance(app_config.vectorstore, VectorStoreConfig)
        assert app_config.vectorstore.distance_metric in ("cosine", "l2", "ip")

    def test_ingestion_config(self, app_config: AppConfig):
        assert isinstance(app_config.ingestion, IngestionConfig)
        assert app_config.ingestion.chunk_size > 0
        assert app_config.ingestion.chunk_overlap >= 0
        assert ".pdf" in app_config.ingestion.supported_extensions

    def test_retrieval_config(self, app_config: AppConfig):
        assert isinstance(app_config.retrieval, RetrievalConfig)
        assert app_config.retrieval.top_k > 0
        assert 0 <= app_config.retrieval.score_threshold <= 1

    def test_branding_config(self, app_config: AppConfig):
        assert isinstance(app_config.branding, BrandingConfig)
        assert app_config.branding.product_name

    def test_load_config_with_nonexistent_path_uses_defaults(self):
        result = load_config(config_path=Path("/nonexistent/settings.yaml"))
        assert isinstance(result, AppConfig)
        assert result.app_name == "Anchorpoint"
