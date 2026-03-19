"""
Property-based tests for the Lambda ingestion handler.

**Validates: Requirements 7.9**

Property 6: Lambda ingestion handler processes S3 events
For any valid S3 ObjectCreated event containing a supported document type
at a well-formed S3 key, the handler should download the document, run the
ingestion pipeline, and produce at least one chunk with correct document_id
and tenant_id.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

from hypothesis import given, settings, assume
from hypothesis import strategies as st

from src.lambda_handlers.ingestion_handler import (
    _process_record,
    SUPPORTED_EXTENSIONS,
)


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_uuid_st = st.from_regex(
    r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
    fullmatch=True,
)

_extension_st = st.sampled_from(sorted(SUPPORTED_EXTENSIONS))

# Filenames: 1-60 printable chars (no slashes) + supported extension
_filename_st = st.builds(
    lambda base, ext: base + ext,
    base=st.text(
        alphabet=st.characters(
            whitelist_categories=("L", "N", "P", "S", "Z"),
            blacklist_characters="/\x00",
        ),
        min_size=1,
        max_size=60,
    ),
    ext=_extension_st,
)

_bucket_st = st.just("industrial-dev-documents-666666666666")


def _make_sqs_record(tenant_id: str, doc_id: str, filename: str, bucket: str) -> dict:
    key = f"tenants/{tenant_id}/uploads/{doc_id}/{filename}"
    s3_body = {
        "Records": [{
            "s3": {
                "bucket": {"name": bucket},
                "object": {"key": key},
            }
        }]
    }
    return {"body": json.dumps(s3_body)}


# ---------------------------------------------------------------------------
# Property 6: Lambda ingestion handler processes S3 events
# ---------------------------------------------------------------------------

# Feature: aws-cdk-deployment, Property 6: Lambda ingestion handler processes S3 events

class TestProperty6LambdaIngestionHandler:
    """
    **Validates: Requirements 7.9**

    For any valid S3 ObjectCreated event with a supported document type and
    well-formed S3 key, the handler downloads the document, runs the pipeline,
    and produces at least one chunk with correct identifiers.
    """

    @given(
        tenant_id=_uuid_st,
        doc_id=_uuid_st,
        filename=_filename_st,
        bucket=_bucket_st,
        chunk_count=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=100, deadline=None)
    @patch("src.lambda_handlers.ingestion_handler._download_from_s3")
    @patch("src.lambda_handlers.ingestion_handler.get_session_factory")
    @patch("src.lambda_handlers.ingestion_handler.load_config")
    @patch("src.lambda_handlers.ingestion_handler.create_embedding_provider")
    @patch("src.lambda_handlers.ingestion_handler.PostgresVectorStore")
    @patch("src.lambda_handlers.ingestion_handler.IngestionPipeline")
    def test_valid_s3_event_produces_chunks(
        self,
        mock_pipeline_cls,
        mock_vs_cls,
        mock_embedder_fn,
        mock_config_fn,
        mock_sf,
        mock_download,
        tenant_id,
        doc_id,
        filename,
        bucket,
        chunk_count,
    ):
        # Ensure filename doesn't contain only whitespace before the extension
        assume(filename.rsplit(".", 1)[0].strip())

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
        mock_result.total_chunks = chunk_count
        mock_pipeline_cls.return_value.ingest_file.return_value = mock_result

        record = _make_sqs_record(tenant_id, doc_id, filename, bucket)
        result_chunks = _process_record(record)

        # Property: chunks produced >= 1
        assert result_chunks >= 1
        assert result_chunks == chunk_count

        # Property: pipeline was called with correct document_id
        call_args = mock_pipeline_cls.return_value.ingest_file.call_args
        assert call_args[1]["document_id"] == doc_id

        # Property: S3 download was called with correct bucket and key
        dl_args = mock_download.call_args
        assert dl_args[0][0] == bucket
        expected_key = f"tenants/{tenant_id}/uploads/{doc_id}/{filename}"
        assert dl_args[0][1] == expected_key

        # Property: vector store created with correct tenant_id
        vs_call = mock_vs_cls.call_args
        assert vs_call[1]["tenant_id"] == tenant_id
