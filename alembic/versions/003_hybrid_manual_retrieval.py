"""Hybrid retrieval + parent-child: document_parents, chunks columns (tsv, section_path, etc.), HNSW/GIN indexes, backfill.

Revision ID: 003
Revises: 002
Create Date: 2025-02-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Create document_parents table
    op.create_table(
        "document_parents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("section_path", sa.Text(), nullable=True),
        sa.Column("text_parent", sa.Text(), nullable=False),
        sa.Column("page_start", sa.Integer(), nullable=True),
        sa.Column("page_end", sa.Integer(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_document_parents_tenant_id", "document_parents", ["tenant_id"])
    op.create_index("idx_document_parents_document_id", "document_parents", ["document_id"])
    # tsvector column and GIN index via raw SQL
    op.execute("ALTER TABLE document_parents ADD COLUMN IF NOT EXISTS tsv tsvector")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_document_parents_tsv_gin ON document_parents USING gin(tsv)"
    )

    # 2) Add columns to document_chunks (all nullable for backfill)
    op.add_column("document_chunks", sa.Column("section_path", sa.Text(), nullable=True))
    op.add_column("document_chunks", sa.Column("page_start", sa.Integer(), nullable=True))
    op.add_column("document_chunks", sa.Column("page_end", sa.Integer(), nullable=True))
    op.add_column("document_chunks", sa.Column("content_type", sa.String(64), nullable=True))
    op.add_column("document_chunks", sa.Column("model_number", sa.String(256), nullable=True))
    op.add_column(
        "document_chunks",
        sa.Column("part_numbers", postgresql.ARRAY(sa.Text()), nullable=True),
    )
    op.add_column(
        "document_chunks",
        sa.Column("error_codes", postgresql.ARRAY(sa.Text()), nullable=True),
    )
    op.add_column(
        "document_chunks",
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_document_chunks_parent_id",
        "document_chunks",
        "document_parents",
        ["parent_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.execute("ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS tsv tsvector")

    # 3) Drop old IVFFLAT index, create HNSW
    op.execute("DROP INDEX IF EXISTS idx_chunks_embedding")
    op.execute(
        "CREATE INDEX idx_chunks_embedding_hnsw ON document_chunks "
        "USING hnsw (embedding vector_cosine_ops)"
    )

    # 4) GIN index on document_chunks.tsv
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_document_chunks_tsv_gin ON document_chunks USING gin(tsv)"
    )

    # 5) Backfill tsv for existing rows (english config; empty string -> empty tsvector)
    op.execute(
        "UPDATE document_chunks SET tsv = to_tsvector('english', coalesce(text, '')) WHERE tsv IS NULL"
    )
    op.execute(
        "UPDATE document_parents SET tsv = to_tsvector('english', coalesce(text_parent, '')) WHERE tsv IS NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_document_chunks_tsv_gin")
    op.execute("DROP INDEX IF EXISTS idx_chunks_embedding_hnsw")
    op.execute("ALTER TABLE document_chunks DROP COLUMN IF EXISTS tsv")
    op.drop_constraint("fk_document_chunks_parent_id", "document_chunks", type_="foreignkey")
    op.drop_column("document_chunks", "parent_id")
    op.drop_column("document_chunks", "error_codes")
    op.drop_column("document_chunks", "part_numbers")
    op.drop_column("document_chunks", "model_number")
    op.drop_column("document_chunks", "content_type")
    op.drop_column("document_chunks", "page_end")
    op.drop_column("document_chunks", "page_start")
    op.drop_column("document_chunks", "section_path")
    op.execute("DROP INDEX IF EXISTS idx_document_parents_tsv_gin")
    op.execute("ALTER TABLE document_parents DROP COLUMN IF EXISTS tsv")
    op.drop_index("idx_document_parents_document_id", table_name="document_parents")
    op.drop_index("idx_document_parents_tenant_id", table_name="document_parents")
    op.drop_table("document_parents")
    # Restore IVFFLAT for compatibility
    op.execute(
        "CREATE INDEX idx_chunks_embedding ON document_chunks "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )
