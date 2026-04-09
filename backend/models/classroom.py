import uuid

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, UniqueConstraint
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
    class_code = Column(String(10), unique=True, nullable=False, index=True)

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
        UniqueConstraint("classroom_id", "student_id", name="uq_classroom_student"),
    )

    classroom = relationship("Classroom", back_populates="memberships")
    student = relationship("User", back_populates="memberships")

    def __repr__(self) -> str:
        return (
            f"<ClassroomMembership classroom={self.classroom_id} "
            f"student={self.student_id}>"
        )
