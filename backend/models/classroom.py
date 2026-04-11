import uuid

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base, SoftDeleteMixin, TimestampMixin


class Classroom(TimestampMixin, SoftDeleteMixin, Base):
    """
    A course created by a professor.
    class_code is a random 6-character alphanumeric code.
    """

    __tablename__ = "classrooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    professor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    class_name = Column(String(200), nullable=False)
    class_code = Column(String(10), unique=True, nullable=False)

    professor = relationship("User", foreign_keys=[professor_id])
    memberships = relationship(
        "ClassroomMembership",
        back_populates="classroom",
        cascade="all, delete-orphan",
    )
    tasks = relationship(
        "AssignmentTask",
        back_populates="classroom",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Classroom name={self.class_name!r} code={self.class_code}>"


class ClassroomMembership(TimestampMixin, SoftDeleteMixin, Base):
    """Junction table: which students are enrolled in which classroom."""

    __tablename__ = "classroom_memberships"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    classroom_id = Column(
        UUID(as_uuid=True),
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        # Partial unique index — enforces uniqueness only among active (non-deleted) rows.
        # WHY text() and not (SoftDeleteMixin.is_deleted == False):
        #   is_deleted is not in scope inside the class body; it lives on the mixin.
        #   Using text() passes the condition directly to PostgreSQL, bypassing Python scoping.
        # FAILURE TEST: Without this, a soft-deleted student who rejoins gets an
        #   IntegrityError from the old blanket UNIQUE constraint, locking them out forever.
        Index(
            "uq_active_classroom_student",
            "classroom_id",
            "student_id",
            unique=True,
            postgresql_where=text("is_deleted = FALSE"),
        ),
    )

    classroom = relationship("Classroom", back_populates="memberships")
    student = relationship("User", back_populates="memberships")

    def __repr__(self) -> str:
        return (
            f"<ClassroomMembership classroom={self.classroom_id} "
            f"student={self.student_id}>"
        )
