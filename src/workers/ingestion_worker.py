"""
Background ingestion worker: polls Postgres job queue, runs IngestionPipeline,
stores chunks in pgvector, updates document and job status.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.config import load_config
from src.db.connection import get_session_factory
from src.ingestion.pipeline import IngestionPipeline
from src.llm.factory import create_embedding_provider
from src.vectorstore.pgvector_store import PostgresVectorStore

logger = logging.getLogger(__name__)

POLL_INTERVAL_SEC = 5


def _get_pending_jobs(session: Session, limit: int = 10) -> list[tuple]:
    """Fetch pending ingestion jobs (tenant_id, job_id, document_id, file_path, filename)."""
    result = session.execute(
        text("""
            SELECT j.id, j.tenant_id, j.document_id, j.metadata->>'file_path' AS file_path, j.metadata->>'filename' AS filename
            FROM ingestion_jobs j
            WHERE j.status = 'pending'
            ORDER BY j.created_at
            LIMIT :limit
            FOR UPDATE SKIP LOCKED
        """),
        {"limit": limit},
    )
    return result.fetchall()


def _mark_processing(session: Session, job_id: UUID) -> None:
    session.execute(
        text("UPDATE ingestion_jobs SET status = 'processing', started_at = now() WHERE id = :id"),
        {"id": str(job_id)},
    )
    session.commit()


def _mark_completed(session: Session, job_id: UUID, document_id: UUID, chunk_count: int) -> None:
    session.execute(
        text("""
            UPDATE ingestion_jobs SET status = 'completed', completed_at = now() WHERE id = :id
        """),
        {"id": str(job_id)},
    )
    session.execute(
        text("""
            UPDATE documents SET status = 'completed', chunk_count = :chunk_count, ingested_at = now() WHERE id = :id
        """),
        {"id": str(document_id), "chunk_count": chunk_count},
    )
    session.commit()


def _mark_failed(session: Session, job_id: UUID, document_id: UUID, error: str) -> None:
    session.execute(
        text("""
            UPDATE ingestion_jobs SET status = 'failed', completed_at = now(), error_message = :err WHERE id = :id
        """),
        {"id": str(job_id), "err": error[:4096]},
    )
    session.execute(
        text("UPDATE documents SET status = 'failed' WHERE id = :id"),
        {"id": str(document_id)},
    )
    session.commit()


def process_one_job(
    job_id: UUID,
    tenant_id: UUID,
    document_id: UUID,
    file_path: str,
    filename: str,
) -> int:
    """Run ingestion for one job. Returns chunk count on success."""
    config = load_config()
    session_factory = get_session_factory()
    embedder = create_embedding_provider(config.embedding)
    vector_store = PostgresVectorStore(
        tenant_id=str(tenant_id),
        session_factory=session_factory,
        embedding_model=config.embedding.model,
        embedding_version=1,
    )
    pipeline = IngestionPipeline(
        embedding_provider=embedder,
        vector_store=vector_store,
        chunk_size=config.ingestion.chunk_size,
        chunk_overlap=config.ingestion.chunk_overlap,
        min_chunk_words=getattr(config.ingestion, "min_chunk_words", 15),
    )
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Upload file not found: {file_path}")
    result = pipeline.ingest_file(path, document_id=str(document_id))
    if result.status != "success":
        raise RuntimeError(result.error_message or "Ingestion failed")
    return result.total_chunks


def run_ingestion_worker(poll_interval: float = POLL_INTERVAL_SEC) -> None:
    """Main loop: poll pending jobs, process each, update status."""
    logger.info("Ingestion worker started")
    session_factory = get_session_factory()

    while True:
        try:
            session = session_factory()
            try:
                rows = _get_pending_jobs(session, limit=10)
            finally:
                session.close()

            for row in rows:
                job_id, tenant_id, document_id, file_path, filename = row[0], row[1], row[2], row[3], row[4]
                if not file_path or not document_id:
                    sess = session_factory()
                    try:
                        sess.execute(
                            text("UPDATE ingestion_jobs SET status = 'failed', error_message = :err WHERE id = :id"),
                            {"id": str(job_id), "err": "Missing file_path or document_id"},
                        )
                        sess.commit()
                    finally:
                        sess.close()
                    continue
                sess = session_factory()
                try:
                    _mark_processing(sess, UUID(str(job_id)))
                finally:
                    sess.close()

                try:
                    chunk_count = process_one_job(
                        UUID(str(job_id)),
                        UUID(str(tenant_id)),
                        UUID(str(document_id)),
                        file_path,
                        filename or "document",
                    )
                    sess = session_factory()
                    try:
                        _mark_completed(sess, UUID(str(job_id)), UUID(str(document_id)), chunk_count)
                    finally:
                        sess.close()
                    logger.info(f"Job {job_id} completed: {chunk_count} chunks")
                except Exception as e:
                    logger.exception(f"Job {job_id} failed: {e}")
                    sess = session_factory()
                    try:
                        _mark_failed(sess, UUID(str(job_id)), UUID(str(document_id)), str(e))
                    finally:
                        sess.close()

        except Exception as e:
            logger.exception(f"Worker loop error: {e}")

        time.sleep(poll_interval)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_ingestion_worker()
