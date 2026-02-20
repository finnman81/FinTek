"""Initial schema: pgvector extension, tenants, users, documents, document_chunks, ingestion_jobs, usage_logs, tenant_usage_limits, embedding_versions.

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Tenants
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"], unique=True)

    # Users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("role", sa.String(32), nullable=False, server_default="user"),
        sa.Column("clerk_user_id", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
    )
    op.create_index("ix_users_clerk_user_id", "users", ["clerk_user_id"], unique=True)

    # Documents
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("s3_key", sa.String(1024), nullable=False),
        sa.Column("file_type", sa.String(32), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("chunk_count", sa.Integer(), server_default="0"),
        sa.Column("embedding_model", sa.String(128), nullable=True),
        sa.Column("embedding_version", sa.Integer(), server_default="1"),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
    )

    # Document chunks (with vector column via raw SQL for pgvector)
    op.create_table(
        "document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding_model", sa.String(128), nullable=False, server_default="text-embedding-3-small"),
        sa.Column("embedding_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
    )
    op.execute("ALTER TABLE document_chunks ADD COLUMN embedding vector(1536)")
    op.create_index("idx_document_chunks_tenant_id", "document_chunks", ["tenant_id"])
    op.execute(
        "CREATE INDEX idx_chunks_embedding ON document_chunks "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )

    # Ingestion jobs
    op.create_table(
        "ingestion_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
    )
    op.execute(
        "CREATE INDEX idx_ingestion_jobs_pending ON ingestion_jobs(tenant_id, status, created_at) "
        "WHERE status = 'pending'"
    )

    # Usage logs
    op.create_table(
        "usage_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("endpoint", sa.String(256), nullable=False),
        sa.Column("model", sa.String(128), nullable=False),
        sa.Column("tokens_used", sa.Integer(), nullable=False),
        sa.Column("cost_estimate", sa.Numeric(10, 4), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index("idx_usage_logs_tenant_date", "usage_logs", ["tenant_id", "created_at"])

    # Tenant usage limits
    op.create_table(
        "tenant_usage_limits",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("monthly_token_limit", sa.Integer(), nullable=True),
        sa.Column("daily_token_limit", sa.Integer(), nullable=True),
        sa.Column("current_month_tokens", sa.Integer(), server_default="0"),
        sa.Column("current_day_tokens", sa.Integer(), server_default="0"),
        sa.Column("last_reset_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cap_type", sa.String(16), server_default="soft"),
        sa.PrimaryKeyConstraint("tenant_id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
    )

    # Embedding versions
    op.create_table(
        "embedding_versions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("model_name", sa.String(128), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("dimensions", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("uq_embedding_versions_model_version", "embedding_versions", ["model_name", "version"], unique=True)


def downgrade() -> None:
    op.drop_table("embedding_versions")
    op.drop_table("tenant_usage_limits")
    op.drop_table("usage_logs")
    op.drop_table("ingestion_jobs")
    op.drop_table("document_chunks")
    op.drop_table("documents")
    op.drop_table("users")
    op.drop_table("tenants")
    op.execute("DROP EXTENSION IF EXISTS vector")
