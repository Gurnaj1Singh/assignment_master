import uuid

from sqlalchemy import Column, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, SoftDeleteMixin, TimestampMixin


class AssignmentTask(TimestampMixin, SoftDeleteMixin, Base):
    """
    A specific assignment posted inside a classroom by a professor.
    assignment_code is a unique 6-char code for submission identification.
    """

    __tablename__ = "assignment_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    classroom_id = Column(
        UUID(as_uuid=True),
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(300), nullable=False)
    assignment_code = Column(String(10), unique=True, nullable=False)

    classroom = relationship("Classroom", back_populates="tasks")
    submissions = relationship(
        "Submission",
        back_populates="task",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<AssignmentTask title={self.title!r} code={self.assignment_code}>"


class Submission(TimestampMixin, SoftDeleteMixin, Base):
    """
    Tracks a student's PDF submission for a specific assignment task.

    overall_similarity_score: percentage of sentences matching other submissions.
    (0.0 = clean, 100.0 = fully plagiarised)
    status: pending -> processing -> completed -> failed
    """

    __tablename__ = "submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("assignment_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    overall_similarity_score = Column(Float, default=0.0, nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    file_path = Column(Text, nullable=False)

    task = relationship("AssignmentTask", back_populates="submissions")
    student = relationship("User", back_populates="submissions")
    vectors = relationship(
        "TextVector",
        back_populates="submission",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Submission id={self.id} student={self.student_id} "
            f"score={self.overall_similarity_score}%>"
        )
