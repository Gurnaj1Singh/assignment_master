"""Add reference corpus tables (reference_documents, reference_vectors).

Changes applied:
  1. Create reference_documents table (UUID PK, soft-deletable, timestamped)
  2. Create reference_vectors table (BigInteger PK, CASCADE from reference_documents)
  3. Add composite index on (reference_id, type) for fast lookup

NOTE: The text_chunk_type ENUM already exists from migration 003.
      We reference it but do NOT re-create it.

Revision ID: 004
Revises: 003
Create Date: 2026-04-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. reference_documents — professor-uploaded reference PDFs per task
    # ------------------------------------------------------------------
    op.create_table(
        "reference_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assignment_tasks.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column(
            "uploaded_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # TimestampMixin columns
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        # SoftDeleteMixin columns
        sa.Column("is_deleted", sa.Boolean, default=False, nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_refdoc_is_deleted", "reference_documents", ["is_deleted"])

    # ------------------------------------------------------------------
    # 2. reference_vectors — SBERT embeddings for reference document chunks
    #    Uses the existing text_chunk_type ENUM (created in migration 003).
    # ------------------------------------------------------------------
    op.create_table(
        "reference_vectors",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "reference_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("reference_documents.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("content_chunk", sa.Text, nullable=False),
        # Both embedding and type are created as plain types then altered via
        # raw SQL — pgvector's vector(768) and PostgreSQL ENUM types are not
        # natively emittable by SQLAlchemy DDL without side-effects.
        sa.Column("embedding", sa.Text, nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("seq_order", sa.Integer, nullable=False),
    )

    # Convert embedding column to vector(768)
    op.execute(
        "ALTER TABLE reference_vectors "
        "ALTER COLUMN embedding TYPE vector(768) USING embedding::vector"
    )

    # Convert type column to the existing text_chunk_type ENUM (created in 003)
    op.execute(
        "ALTER TABLE reference_vectors "
        "ALTER COLUMN type TYPE text_chunk_type USING type::text_chunk_type"
    )

    # ------------------------------------------------------------------
    # 3. Composite index on (reference_id, type) — fast sentence/paragraph
    #    lookup without scanning all types for a given reference.
    # ------------------------------------------------------------------
    op.create_index("ix_rv_reference_type", "reference_vectors", ["reference_id", "type"])


def downgrade() -> None:
    op.drop_index("ix_rv_reference_type", table_name="reference_vectors")
    op.drop_table("reference_vectors")
    op.drop_index("ix_refdoc_is_deleted", table_name="reference_documents")
    op.drop_table("reference_documents")
