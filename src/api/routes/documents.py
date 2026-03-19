"""
Document routes: upload (creates job), list, status, delete.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import List

import boto3
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from src.api.deps import get_current_tenant_id, get_db
from src.api.models.documents import DocumentInfo, DocumentStatusResponse, UploadResponse
from src.db.models import Document, IngestionJob

router = APIRouter()


@router.get("", response_model=List[DocumentInfo])
def list_documents(
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """List documents for the current tenant."""
    from uuid import UUID
    docs = db.query(Document).filter(Document.tenant_id == UUID(tenant_id)).order_by(Document.created_at.desc()).all()
    return [
        DocumentInfo(
            id=str(d.id),
            filename=d.filename,
            file_type=d.file_type,
            status=d.status,
            chunk_count=d.chunk_count or 0,
            created_at=d.created_at,
        )
        for d in docs
    ]


def _get_s3_client():
    """Return a boto3 S3 client. Extracted for testability."""
    return boto3.client("s3")


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """Upload a file to S3 and create an ingestion job. Returns immediately; Lambda processes async."""
    from uuid import UUID
    from src.db.models import Tenant

    tid = UUID(tenant_id)
    tenant = db.query(Tenant).filter(Tenant.id == tid).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    bucket_name = os.environ.get("S3_BUCKET_NAME")
    if not bucket_name:
        raise HTTPException(status_code=500, detail="S3_BUCKET_NAME not configured")

    doc_id = uuid.uuid4()
    job_id = uuid.uuid4()
    filename = file.filename or "document"
    s3_key = f"tenants/{tid}/uploads/{doc_id}/{filename}"

    s3_client = _get_s3_client()
    s3_client.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=content,
    )

    doc = Document(
        id=doc_id,
        tenant_id=tid,
        filename=filename,
        s3_key=s3_key,
        file_type=Path(filename).suffix or "",
        status="pending",
    )
    db.add(doc)

    job = IngestionJob(
        id=job_id,
        tenant_id=tid,
        document_id=doc_id,
        status="pending",
        metadata_={"s3_key": s3_key, "filename": filename},
    )
    db.add(job)
    db.commit()

    return UploadResponse(
        document_id=str(doc_id),
        job_id=str(job_id),
    )


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
def document_status(
    document_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """Return ingestion job status for a document."""
    from uuid import UUID
    try:
        did = UUID(document_id)
        tid = UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID")

    doc = db.query(Document).filter(Document.id == did, Document.tenant_id == tid).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    job = db.query(IngestionJob).filter(IngestionJob.document_id == did).order_by(IngestionJob.created_at.desc()).first()
    error = job.error_message if job else None
    status = doc.status if doc else "pending"
    if job:
        status = job.status

    return DocumentStatusResponse(
        document_id=document_id,
        status=status,
        error_message=error,
    )


@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """Delete a document and its chunks (vector store delete is done via worker or inline)."""
    from uuid import UUID
    try:
        did = UUID(document_id)
        tid = UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID")

    doc = db.query(Document).filter(Document.id == did, Document.tenant_id == tid).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete chunks (cascade or explicit) and document
    db.delete(doc)
    db.commit()
    return {"status": "deleted", "document_id": document_id}
