"""
Base model and reusable mixins for all SQLAlchemy models.

TimestampMixin  — adds created_at / updated_at (auto-managed).
SoftDeleteMixin — adds is_deleted flag; repositories filter by default.
"""

from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class TimestampMixin:
    """Auto-managed created_at and updated_at columns."""

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """Logical deletion — rows are never physically removed."""

    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at  = Column(DateTime(timezone=True), nullable=True)
    deleted_by  = Column(PG_UUID(as_uuid=True), nullable=True)
