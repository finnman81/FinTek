"""
SQLAlchemy models for Anchorpoint.

Includes: Tenant, User, Document, DocumentChunk (with pgvector), IngestionJob,
UsageLog, TenantUsageLimits, EmbeddingVersion.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = None  # type: ignore; pgvector required for production

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


def uuid4_str():
    return str(uuid.uuid4())


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(64), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    users = relationship("User", back_populates="tenant")
    documents = relationship("Document", back_populates="tenant")


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(String(32), nullable=False, default="user")  # admin, user
    clerk_user_id = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="users")


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    filename = Column(String(512), nullable=False)
    s3_key = Column(String(1024), nullable=False)
    file_type = Column(String(32), nullable=False)
    ingested_at = Column(DateTime(timezone=True))
    chunk_count = Column(Integer, default=0)
    embedding_model = Column(String(128))
    embedding_version = Column(Integer, default=1)
    status = Column(String(32), nullable=False, default="pending")  # pending, processing, completed, failed
    metadata_ = Column("metadata", JSONB)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    parents = relationship("DocumentParent", back_populates="document", cascade="all, delete-orphan")


class DocumentParent(Base):
    """Parent chunk (section-level) for manual-friendly retrieval. Children reference this."""

    __tablename__ = "document_parents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    section_path = Column(Text, nullable=True)
    text_parent = Column(Text, nullable=False)
    page_start = Column(Integer, nullable=True)
    page_end = Column(Integer, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    document = relationship("Document", back_populates="parents")
    children = relationship("DocumentChunk", back_populates="parent", foreign_keys="DocumentChunk.parent_id")

    __table_args__ = (
        Index("idx_document_parents_tenant_id", "tenant_id"),
        Index("idx_document_parents_document_id", "document_id"),
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    embedding = Column(Vector(1536)) if Vector else Column(JSONB)  # type: ignore
    embedding_model = Column(String(128), nullable=False, default="text-embedding-3-small")
    embedding_version = Column(Integer, nullable=False, default=1)
    metadata_ = Column("metadata", JSONB)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    section_path = Column(Text, nullable=True)
    page_start = Column(Integer, nullable=True)
    page_end = Column(Integer, nullable=True)
    content_type = Column(String(64), nullable=True)  # procedure, warning, spec, table
    part_numbers = Column(ARRAY(Text), nullable=True)
    error_codes = Column(ARRAY(Text), nullable=True)
    model_number = Column(String(256), nullable=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("document_parents.id", ondelete="SET NULL"), nullable=True)

    document = relationship("Document", back_populates="chunks")
    parent = relationship("DocumentParent", back_populates="children", foreign_keys=[parent_id])

    __table_args__ = (
        Index("idx_document_chunks_tenant_id", "tenant_id"),
    )


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    status = Column(String(32), nullable=False, default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    metadata_ = Column("metadata", JSONB)

    __table_args__ = (
        Index(
            "idx_ingestion_jobs_pending",
            "tenant_id",
            "status",
            "created_at",
            postgresql_where=text("status = 'pending'"),
        ),
    )


class UsageLog(Base):
    __tablename__ = "usage_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    endpoint = Column(String(256), nullable=False)
    model = Column(String(128), nullable=False)
    tokens_used = Column(Integer, nullable=False)
    cost_estimate = Column(Numeric(10, 4))
    latency_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


Index("idx_usage_logs_tenant_date", UsageLog.tenant_id, UsageLog.created_at)


class TenantUsageLimits(Base):
    __tablename__ = "tenant_usage_limits"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), primary_key=True)
    monthly_token_limit = Column(Integer)
    daily_token_limit = Column(Integer)
    current_month_tokens = Column(Integer, default=0)
    current_day_tokens = Column(Integer, default=0)
    last_reset_date = Column(DateTime(timezone=True))
    cap_type = Column(String(16), default="soft")  # soft (warn), hard (block)


class ResponseRating(Base):
    """User rating (1-5) for a chat response. Used for refinement / eval."""

    __tablename__ = "response_ratings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    question = Column(Text, nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    answer = Column(Text, nullable=True)  # optional, for low-rated analysis
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (Index("idx_response_ratings_tenant_date", "tenant_id", "created_at"),)


class EmbeddingVersion(Base):
    __tablename__ = "embedding_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(128), nullable=False)
    version = Column(Integer, nullable=False)
    dimensions = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("uq_embedding_versions_model_version", "model_name", "version", unique=True),
    )
