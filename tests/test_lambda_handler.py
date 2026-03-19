"""
Unit tests for the Lambda ingestion handler.

Tests cover: S3 key parsing, extension validation, successful ingestion flow,
and error handling (missing key, unsupported format, DB failure).
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.lambda_handlers.ingestion_handler import (
    _parse_s3_key,
    _validate_extension,
    handler,
    _process_record,
    SUPPORTED_EXTENSIONS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TENANT_ID = str(uuid.uuid4())
DOC_ID = str(uuid.uuid4())
BUCKET = "industrial-dev-documents-666666666666"


def _make_sqs_event(key: str, bucket: str = BUCKET) -> dict:
    """Build a minimal SQS event wrapping an S3 notification."""
    s3_body = {
        "Records": [{
            "s3": {
                "bucket": {"name": bucket},
                "object": {"key": key},
            }
        }]
    }
    return {
        "Records": [{
            "body": json.dumps(s3_body),
        }]
    }


# ---------------------------------------------------------------------------
# S3 key parsing
# ---------------------------------------------------------------------------

class TestParseS3Key:
    def test_valid_key(self):
        tid, did, fname = _parse_s3_key(
            f"tenants/{TENANT_ID}/uploads/{DOC_ID}/manual.pdf"
        )
        assert tid == TENANT_ID
        assert did == DOC_ID
        assert fname == "manual.pdf"

    def test_filename_with_spaces(self):
        tid, did, fname = _parse_s3_key(
            f"tenants/{TENANT_ID}/uploads/{DOC_ID}/my document.pdf"
        )
        assert fname == "my document.pdf"

    def test_invalid_key_raises(self):
        with pytest.raises(ValueError, match="does not match"):
            _parse_s3_key("bad/key/format.pdf")

    def test_missing_filename_raises(self):
        with pytest.raises(ValueError, match="does not match"):
            _parse_s3_key(f"tenants/{TENANT_ID}/uploads/{DOC_ID}/")


# ---------------------------------------------------------------------------
# Extension validation
# ---------------------------------------------------------------------------

class TestValidateExtension:
    def test_supported_extensions(self):
        for ext in SUPPORTED_EXTENSIONS:
            fname = f"doc{ext}"
            result = _validate_extension(fname)
            assert result == ext

    def test_unsupported_extension_raises(self):
        with pytest.raises(ValueError, match="Unsupported"):
            _validate_extension("file.xyz")

    def test_case_insensitive(self):
        result = _validate_extension("DOC.TXT")
        assert result == ".txt"


# ---------------------------------------------------------------------------
# Full handler flow (mocked dependencies)
# ---------------------------------------------------------------------------

class TestProcessRecord:
    """Test _process_record with mocked S3, DB, and pipeline."""

    def _make_record(self, filename="manual.txt"):
        key = f"tenants/{TENANT_ID}/uploads/{DOC_ID}/{filename}"
        s3_body = {
            "Records": [{
                "s3": {
                    "bucket": {"name": BUCKET},
                    "object": {"key": key},
                }
            }]
        }
        return {"body": json.dumps(s3_body)}

    @patch("src.lambda_handlers.ingestion_handler._download_from_s3")
    @patch("src.lambda_handlers.ingestion_handler.get_session_factory")
    @patch("src.lambda_handlers.ingestion_handler.load_config")
    @patch("src.lambda_handlers.ingestion_handler.create_embedding_provider")
    @patch("src.lambda_handlers.ingestion_handler.PostgresVectorStore")
    @patch("src.lambda_handlers.ingestion_handler.IngestionPipeline")
    def test_successful_ingestion(
        self, mock_pipeline_cls, mock_vs_cls, mock_embedder_fn,
        mock_config_fn, mock_sf, mock_download,
    ):
        # Setup mocks
        mock_session = MagicMock()
        mock_sf.return_value = MagicMock(return_value=mock_session)

        mock_config = MagicMock()
        mock_config.embedding.model = "text-embedding-3-small"
        mock_config.ingestion.chunk_size = 1000
        mock_config.ingestion.chunk_overlap = 200
        mock_config_fn.return_value = mock_config

        mock_result = MagicMock()
        mock_result.status = "success"
        mock_result.total_chunks = 5
        mock_pipeline_cls.return_value.ingest_file.return_value = mock_result

        record = self._make_record()
        chunks = _process_record(record)

        assert chunks == 5
        mock_download.assert_called_once()
        mock_pipeline_cls.return_value.ingest_file.assert_called_once()
        # Verify DB calls happened (document row + job row + completed)
        assert mock_session.execute.call_count >= 3
        assert mock_session.commit.call_count >= 3


    @patch("src.lambda_handlers.ingestion_handler._download_from_s3")
    @patch("src.lambda_handlers.ingestion_handler.get_session_factory")
    @patch("src.lambda_handlers.ingestion_handler.load_config")
    @patch("src.lambda_handlers.ingestion_handler.create_embedding_provider")
    @patch("src.lambda_handlers.ingestion_handler.PostgresVectorStore")
    @patch("src.lambda_handlers.ingestion_handler.IngestionPipeline")
    def test_pipeline_failure_marks_failed(
        self, mock_pipeline_cls, mock_vs_cls, mock_embedder_fn,
        mock_config_fn, mock_sf, mock_download,
    ):
        mock_session = MagicMock()
        mock_sf.return_value = MagicMock(return_value=mock_session)

        mock_config = MagicMock()
        mock_config.embedding.model = "text-embedding-3-small"
        mock_config.ingestion.chunk_size = 1000
        mock_config.ingestion.chunk_overlap = 200
        mock_config_fn.return_value = mock_config

        mock_result = MagicMock()
        mock_result.status = "error"
        mock_result.error_message = "Parse failed"
        mock_pipeline_cls.return_value.ingest_file.return_value = mock_result

        record = self._make_record()
        with pytest.raises(RuntimeError, match="Parse failed"):
            _process_record(record)

    def test_unsupported_format_raises(self):
        record = self._make_record(filename="data.xyz")
        with pytest.raises(ValueError, match="Unsupported"):
            _process_record(record)

    def test_invalid_s3_key_raises(self):
        s3_body = {
            "Records": [{
                "s3": {
                    "bucket": {"name": BUCKET},
                    "object": {"key": "bad/key.pdf"},
                }
            }]
        }
        record = {"body": json.dumps(s3_body)}
        with pytest.raises(ValueError, match="does not match"):
            _process_record(record)

    def test_empty_s3_records_raises(self):
        record = {"body": json.dumps({"Records": []})}
        with pytest.raises(ValueError, match="No S3 Records"):
            _process_record(record)


# ---------------------------------------------------------------------------
# Top-level handler
# ---------------------------------------------------------------------------

class TestHandler:
    @patch("src.lambda_handlers.ingestion_handler._process_record")
    def test_handler_calls_process_record(self, mock_proc):
        mock_proc.return_value = 3
        event = {"Records": [{"body": "{}"}]}
        handler(event, None)
        mock_proc.assert_called_once_with({"body": "{}"})

    @patch("src.lambda_handlers.ingestion_handler._process_record")
    def test_handler_reraises_on_failure(self, mock_proc):
        mock_proc.side_effect = RuntimeError("boom")
        event = {"Records": [{"body": "{}"}]}
        with pytest.raises(RuntimeError, match="boom"):
            handler(event, None)

    def test_handler_empty_records(self):
        # No records should be a no-op
        handler({"Records": []}, None)
