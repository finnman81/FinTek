"""
AWS Lambda handler for SQS-triggered document ingestion.

Receives S3 ObjectCreated event notifications via SQS, downloads the document,
runs the ingestion pipeline (parse, chunk, embed), and stores results in RDS.

S3 key format: tenants/{tenant_id}/uploads/{document_id}/{filename}
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import boto3
from sqlalchemy import text

from src.db.connection import get_session_factory
from src.ingestion.pipeline import IngestionPipeline
from src.ingestion.parsers import PARSER_REGISTRY
from src.llm.factory import create_embedding_provider
from src.core.config import load_config
from src.vectorstore.pgvector_store import PostgresVectorStore

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

S3_KEY_PATTERN = re.compile(
    r"^tenants/([^/]+)/uploads/([^/]+)/(.+)$"
)

SUPPORTED_EXTENSIONS = set(PARSER_REGISTRY.keys())


def _parse_s3_key(key: str) -> tuple[str, str, str]:
    """Extract tenant_id, document_id, and filename from an S3 key.

    Raises:
        ValueError: If the key does not match the expected pattern.
    """
    match = S3_KEY_PATTERN.match(key)
    if not match:
        raise ValueError(
            f"S3 key does not match expected pattern "
            f"'tenants/{{tenant_id}}/uploads/{{document_id}}/{{filename}}': {key}"
        )
    return match.group(1), match.group(2), match.group(3)


def _validate_extension(filename: str) -> str:
    """Return the lowercase file extension if supported, else raise ValueError."""
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(f"Unsupported file type '{ext}'. Supported: {supported}")
    return ext


def _download_from_s3(bucket: str, key: str, local_path: Path) -> None:
    """Download an object from S3 to a local path."""
    s3 = boto3.client("s3")
    local_path.parent.mkdir(parents=True, exist_ok=True)
    s3.download_file(bucket, key, str(local_path))


def _ensure_document_row(session, tenant_id: str, document_id: str, filename: str, s3_key: str, file_ext: str):
    """Create or update the documents row, set status to 'processing'."""
    session.execute(
        text("""
            INSERT INTO documents (id, tenant_id, filename, s3_key, file_type, status, created_at)
            VALUES (:doc_id, :tid, :fname, :s3key, :ftype, 'processing', :now)
            ON CONFLICT (id) DO UPDATE SET status = 'processing', s3_key = :s3key
        """),
        {
            "doc_id": document_id,
            "tid": tenant_id,
            "fname": filename,
            "s3key": s3_key,
            "ftype": file_ext,
            "now": datetime.now(timezone.utc),
        },
    )
    session.commit()


def _ensure_ingestion_job(session, tenant_id: str, document_id: str) -> str:
    """Create an ingestion_jobs row and return its id."""
    import uuid

    job_id = str(uuid.uuid4())
    session.execute(
        text("""
            INSERT INTO ingestion_jobs (id, tenant_id, document_id, status, created_at)
            VALUES (:jid, :tid, :did, 'processing', :now)
        """),
        {
            "jid": job_id,
            "tid": tenant_id,
            "did": document_id,
            "now": datetime.now(timezone.utc),
        },
    )
    session.commit()
    return job_id


def _mark_completed(session, job_id: str, document_id: str, chunk_count: int):
    """Mark document and job as completed."""
    session.execute(
        text("UPDATE ingestion_jobs SET status = 'completed', completed_at = :now WHERE id = :jid"),
        {"jid": job_id, "now": datetime.now(timezone.utc)},
    )
    session.execute(
        text("UPDATE documents SET status = 'completed', chunk_count = :cc, ingested_at = :now WHERE id = :did"),
        {"did": document_id, "cc": chunk_count, "now": datetime.now(timezone.utc)},
    )
    session.commit()


def _mark_failed(session, job_id: str, document_id: str, error_msg: str):
    """Mark document and job as failed."""
    session.execute(
        text("UPDATE ingestion_jobs SET status = 'failed', completed_at = :now, error_message = :err WHERE id = :jid"),
        {"jid": job_id, "now": datetime.now(timezone.utc), "err": error_msg[:4096]},
    )
    session.execute(
        text("UPDATE documents SET status = 'failed' WHERE id = :did"),
        {"did": document_id},
    )
    session.commit()


def _process_record(record: dict) -> int:
    """Process a single SQS record containing an S3 event notification.

    Returns the number of chunks produced.
    """
    body = json.loads(record["body"])
    s3_records = body.get("Records", [])
    if not s3_records:
        raise ValueError("No S3 Records found in SQS message body")

    s3_info = s3_records[0]["s3"]
    bucket = s3_info["bucket"]["name"]
    key = s3_info["object"]["key"]

    tenant_id, document_id, filename = _parse_s3_key(key)
    file_ext = _validate_extension(filename)

    # Validate UUIDs
    UUID(tenant_id)
    UUID(document_id)

    local_path = Path(f"/tmp/{document_id}/{filename}")
    _download_from_s3(bucket, key, local_path)

    session_factory = get_session_factory()
    session = session_factory()
    job_id = None

    try:
        _ensure_document_row(session, tenant_id, document_id, filename, key, file_ext)
        job_id = _ensure_ingestion_job(session, tenant_id, document_id)

        config = load_config()
        embedder = create_embedding_provider(config.embedding)
        vector_store = PostgresVectorStore(
            tenant_id=tenant_id,
            session_factory=session_factory,
            embedding_model=config.embedding.model,
            embedding_version=1,
        )
        pipeline = IngestionPipeline(
            embedding_provider=embedder,
            vector_store=vector_store,
            chunk_size=config.ingestion.chunk_size,
            chunk_overlap=config.ingestion.chunk_overlap,
        )

        result = pipeline.ingest_file(local_path, document_id=document_id)

        if result.status != "success":
            raise RuntimeError(result.error_message or "Ingestion pipeline failed")

        _mark_completed(session, job_id, document_id, result.total_chunks)
        logger.info(
            "Ingestion complete: tenant=%s doc=%s chunks=%d",
            tenant_id, document_id, result.total_chunks,
        )
        return result.total_chunks

    except Exception:
        if job_id:
            import traceback
            _mark_failed(session, job_id, document_id, traceback.format_exc()[:4096])
        raise
    finally:
        session.close()
        # Clean up temp file
        if local_path.exists():
            local_path.unlink()
        if local_path.parent.exists() and not any(local_path.parent.iterdir()):
            local_path.parent.rmdir()


def handler(event, context):
    """AWS Lambda entry point for SQS-triggered document ingestion."""
    records = event.get("Records", [])
    logger.info("Received %d SQS record(s)", len(records))

    for record in records:
        try:
            _process_record(record)
        except Exception as exc:
            logger.exception("Failed to process SQS record: %s", exc)
            # Re-raise so SQS retries the message
            raise
