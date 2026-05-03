"""Add late submission support to submissions table.

Adds:
  - late_status ENUM ('on_time', 'pending_review', 'accepted', 'rejected')
  - late_decision_at DateTime nullable

Existing rows backfill to 'on_time'.

Revision ID: 007
Revises: 006
Create Date: 2026-05-02
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'late_status_enum') THEN
                CREATE TYPE late_status_enum AS ENUM
                    ('on_time', 'pending_review', 'accepted', 'rejected');
            END IF;
        END
        $$;
        """
    )

    late_status = postgresql.ENUM(
        "on_time", "pending_review", "accepted", "rejected",
        name="late_status_enum",
        create_type=False,
    )

    op.add_column(
        "submissions",
        sa.Column(
            "late_status",
            late_status,
            nullable=False,
            server_default="on_time",
        ),
    )
    op.add_column(
        "submissions",
        sa.Column("late_decision_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("submissions", "late_decision_at")
    op.drop_column("submissions", "late_status")
    op.execute("DROP TYPE late_status_enum")
