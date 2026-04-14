"""Add LLM question generation tables.

Changes applied:
  1. Create question_difficulty ENUM type
  2. Create generated_questions table (UUID PK, soft-deletable, timestamped)
  3. Create student_question_assignments table (BigInteger PK, timestamped)
  4. UniqueConstraint on (student_id, question_id) to prevent duplicate assignments

Revision ID: 005
Revises: 004
Create Date: 2026-04-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Create question_difficulty ENUM
    # ------------------------------------------------------------------
    question_difficulty = postgresql.ENUM(
        "easy", "medium", "hard",
        name="question_difficulty",
        create_type=False,
    )
    op.execute("CREATE TYPE question_difficulty AS ENUM ('easy', 'medium', 'hard')")

    # ------------------------------------------------------------------
    # 2. generated_questions — LLM-generated questions from reference material
    # ------------------------------------------------------------------
    op.create_table(
        "generated_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assignment_tasks.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("question_text", sa.Text, nullable=False),
        sa.Column(
            "difficulty",
            question_difficulty,
            nullable=False,
        ),
        sa.Column("bloom_level", sa.String(50), nullable=False),
        sa.Column("is_selected", sa.Boolean, default=False, nullable=False, server_default="false"),
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
    op.create_index("ix_gq_is_deleted", "generated_questions", ["is_deleted"])

    # ------------------------------------------------------------------
    # 3. student_question_assignments — maps questions to students
    # ------------------------------------------------------------------
    op.create_table(
        "student_question_assignments",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "question_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("generated_questions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assignment_tasks.id", ondelete="CASCADE"),
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
        sa.UniqueConstraint(
            "student_id", "question_id",
            name="uq_student_question_no_duplicate",
        ),
    )


def downgrade() -> None:
    op.drop_table("student_question_assignments")
    op.drop_index("ix_gq_is_deleted", table_name="generated_questions")
    op.drop_table("generated_questions")
    op.execute("DROP TYPE question_difficulty")
