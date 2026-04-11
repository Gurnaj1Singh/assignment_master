"""Production model hardening — ENUMs, new columns, constraints, indexes.

Changes applied:
  1. Create PostgreSQL ENUM types: user_role, submission_status, text_chunk_type
  2. Convert users.role          varchar(20)  → user_role ENUM
  3. Convert submissions.status  varchar(20)  → submission_status ENUM
  4. Convert text_vectors.type   varchar(20)  → text_chunk_type ENUM
  5. Add deleted_at / deleted_by to all soft-delete tables
  6. Add due_date / description / is_published / verbatim_flag to relevant tables
  7. Add CheckConstraint on submissions.overall_similarity_score (0–100)
  8. Add UniqueConstraint: one submission per student per task (among active rows)
  9. Add composite indexes on text_vectors for query performance
  10. Fix classroom_memberships partial unique index (replace blanket with partial)

Revision ID: 003
Revises: 002
Create Date: 2026-04-11
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Create ENUM types in PostgreSQL
    #    These must exist before any column references them.
    # ------------------------------------------------------------------
    op.execute("CREATE TYPE user_role AS ENUM ('student', 'professor')")
    op.execute("CREATE TYPE submission_status AS ENUM ('pending', 'processing', 'completed', 'failed')")
    op.execute("CREATE TYPE text_chunk_type AS ENUM ('sentence', 'paragraph')")

    # ------------------------------------------------------------------
    # 2. Convert users.role from varchar to user_role ENUM
    #    USING clause casts existing string values to the new type.
    #    Any value not in ('student','professor') would fail here — surface
    #    bad data early rather than silently corrupt it.
    # ------------------------------------------------------------------
    op.execute(
        "ALTER TABLE users "
        "ALTER COLUMN role TYPE user_role USING role::user_role"
    )

    # ------------------------------------------------------------------
    # 3. Add soft-delete audit columns to all SoftDeleteMixin tables.
    #    All nullable=True — existing rows don't have deletion metadata.
    # ------------------------------------------------------------------
    soft_delete_tables = [
        "users",
        "classrooms",
        "classroom_memberships",
        "assignment_tasks",
        "submissions",
    ]
    for table in soft_delete_tables:
        op.add_column(table, sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
        op.add_column(table, sa.Column("deleted_by", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))

    # ------------------------------------------------------------------
    # 4. AssignmentTask — new product columns
    # ------------------------------------------------------------------
    op.add_column("assignment_tasks", sa.Column("description", sa.Text, nullable=True))
    op.add_column("assignment_tasks", sa.Column("due_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("assignment_tasks", sa.Column("is_published", sa.Boolean, nullable=False, server_default="false"))
    op.add_column("assignment_tasks", sa.Column("assignment_pdf_path", sa.String(500), nullable=True))

    # ------------------------------------------------------------------
    # 5. Submission — status ENUM conversion, verbatim_flag, file_path fix
    # ------------------------------------------------------------------
    op.execute(
        "ALTER TABLE submissions "
        "ALTER COLUMN status TYPE submission_status USING status::submission_status"
    )
    op.add_column("submissions", sa.Column("verbatim_flag", sa.Boolean, nullable=False, server_default="false"))

    # Change file_path from Text to String(500)
    op.execute("ALTER TABLE submissions ALTER COLUMN file_path TYPE varchar(500)")

    # ------------------------------------------------------------------
    # 6. Submission — CheckConstraint for score range
    # ------------------------------------------------------------------
    op.create_check_constraint(
        "ck_score_range",
        "submissions",
        "overall_similarity_score >= 0.0 AND overall_similarity_score <= 100.0",
    )

    # ------------------------------------------------------------------
    # 7. Submission — partial UniqueConstraint (one active submission per student per task)
    #    WHY partial? Soft-deleted submissions should not block a re-submission.
    # ------------------------------------------------------------------
    op.execute("""
        CREATE UNIQUE INDEX uq_one_submission_per_student
        ON submissions (task_id, student_id)
        WHERE is_deleted = FALSE
    """)

    # ------------------------------------------------------------------
    # 8. TextVector — type ENUM conversion
    # ------------------------------------------------------------------
    op.execute(
        "ALTER TABLE text_vectors "
        "ALTER COLUMN type TYPE text_chunk_type USING type::text_chunk_type"
    )

    # ------------------------------------------------------------------
    # 9. TextVector — composite indexes for query performance
    # ------------------------------------------------------------------
    op.create_index("ix_tv_submission_type", "text_vectors", ["submission_id", "type"])
    op.create_index("ix_tv_submission_order", "text_vectors", ["submission_id", "seq_order"])

    # ------------------------------------------------------------------
    # 10. classroom_memberships — replace blanket UNIQUE with partial UNIQUE
    #     The old constraint (from migration 001) blocked soft-deleted students
    #     from re-joining. The new partial index only enforces uniqueness among
    #     active (non-deleted) rows.
    # ------------------------------------------------------------------
    op.drop_constraint("uq_classroom_student", "classroom_memberships", type_="unique")
    op.execute("""
        CREATE UNIQUE INDEX uq_active_classroom_student
        ON classroom_memberships (classroom_id, student_id)
        WHERE is_deleted = FALSE
    """)

    # Add index on users.role — common query: "get all professors for admin panel"
    op.create_index("ix_users_role", "users", ["role"])


def downgrade() -> None:
    # Reverse in opposite order

    op.drop_index("ix_users_role", table_name="users")
    op.drop_index("uq_active_classroom_student", table_name="classroom_memberships")
    op.create_unique_constraint("uq_classroom_student", "classroom_memberships", ["classroom_id", "student_id"])

    op.drop_index("ix_tv_submission_order", table_name="text_vectors")
    op.drop_index("ix_tv_submission_type", table_name="text_vectors")
    op.execute("ALTER TABLE text_vectors ALTER COLUMN type TYPE varchar(20) USING type::text")

    op.drop_index("uq_one_submission_per_student", table_name="submissions")
    op.drop_constraint("ck_score_range", "submissions", type_="check")
    op.execute("ALTER TABLE submissions ALTER COLUMN file_path TYPE text")
    op.drop_column("submissions", "verbatim_flag")
    op.execute("ALTER TABLE submissions ALTER COLUMN status TYPE varchar(20) USING status::text")

    op.drop_column("assignment_tasks", "assignment_pdf_path")
    op.drop_column("assignment_tasks", "is_published")
    op.drop_column("assignment_tasks", "due_date")
    op.drop_column("assignment_tasks", "description")

    soft_delete_tables = [
        "users", "classrooms", "classroom_memberships", "assignment_tasks", "submissions",
    ]
    for table in soft_delete_tables:
        op.drop_column(table, "deleted_by")
        op.drop_column(table, "deleted_at")

    op.execute("ALTER TABLE users ALTER COLUMN role TYPE varchar(20) USING role::text")

    op.execute("DROP TYPE IF EXISTS text_chunk_type")
    op.execute("DROP TYPE IF EXISTS submission_status")
    op.execute("DROP TYPE IF EXISTS user_role")
