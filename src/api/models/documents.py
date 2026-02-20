from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class DocumentInfo(BaseModel):
    id: str
    filename: str
    file_type: str
    status: str
    chunk_count: int
    created_at: datetime


class DocumentStatusResponse(BaseModel):
    document_id: str
    status: str  # pending, processing, completed, failed
    error_message: str | None = None


class UploadResponse(BaseModel):
    document_id: str
    job_id: str
    message: str = "Ingestion job created. Poll /documents/{document_id}/status for status."
