"""
Assignment task and student submission models.

AssignmentTask — a professor's assignment posted inside a classroom.
Submission     — one student's PDF submission for a task, with plagiarism score.
"""

import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, SoftDeleteMixin, TimestampMixin

# ---------------------------------------------------------------------------
# PostgreSQL ENUM types — defined once, reused across columns.
# WHY ENUM over String?
#   The DB rejects any value not in the set. "COMPLETED", "done", "admin" are
#   impossible. With String(20), a stale script or typo silently stores garbage
#   and every status-check in Python silently returns False.
# FAILURE TEST: String status + future `if submission.status == "completed"` check
#   — a bug writes "Completed" (capital C). The check never passes. That student's
#   report page shows "processing" forever. You spend an hour debugging Python
#   when the bug is in data.
# ---------------------------------------------------------------------------
submission_status = Enum(
    "pending", "processing", "completed", "failed",
    name="submission_status",
)


class AssignmentTask(TimestampMixin, SoftDeleteMixin, Base):
    """
    A specific assignment posted inside a classroom by a professor.

    assignment_code : unique 6-char alphanumeric code for submission lookup.
    due_date        : optional deadline; None means no enforced cutoff.
    is_published    : draft=False (invisible to students), published=True (visible).
    description     : optional rich instructions / rubric for students.
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
    description = Column(Text, nullable=True)
    assignment_code = Column(String(10), unique=True, nullable=False)

    # Relative path to the professor-uploaded question paper PDF.
    # Nullable — some assignments may be description-only (no PDF attachment).
    # WHY relative path? Same reason as Submission.file_path — absolute paths
    # break when the server or storage location changes.
    assignment_pdf_path = Column(String(500), nullable=True)

    # WHY due_date nullable?
    #   Some assignments are open-ended (take-home, portfolio).
    #   Mandatory due_date would break those use cases.
    due_date = Column(DateTime(timezone=True), nullable=True)

    # WHY is_published?
    #   A professor needs time to draft and review a task before students see it.
    #   Without this flag, every saved task is immediately visible — a half-written
    #   assignment appears as a real task. This is the "draft vs live" toggle.
    is_published = Column(Boolean, default=False, nullable=False)

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
    Tracks one student's PDF submission for a specific assignment task.

    overall_similarity_score : 0.0 (clean) to 100.0 (fully plagiarised).
    status                   : pending → processing → completed | failed
    file_path                : relative path from UPLOAD_DIR root.
    verbatim_flag            : True if submission contains word-for-word copying
                               from the reference corpus (Day 2 feature).
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
    status = Column(submission_status, default="pending", nullable=False)

    # Relative path from UPLOAD_DIR — not absolute.
    # WHY relative? Absolute paths break when the server moves or storage changes.
    # FAILURE TEST: Absolute path stored → server migrated to /opt/app → every
    #   file_path points to /home/gsm/... → FileNotFoundError on every report download.
    file_path = Column(String(500), nullable=False)

    # Placeholder for Day 2 verbatim detection feature.
    verbatim_flag = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        # WHY this constraint?
        #   Without it a student can re-submit 50 times (network glitches, double-clicks).
        #   Each submission creates N TextVector rows. The task's plagiarism pool grows
        #   with duplicate data from the same student, inflating everyone's scores.
        # WHY UniqueConstraint and not application-level check?
        #   The application check has a TOCTOU race condition — two simultaneous requests
        #   both read "no existing submission", both pass validation, both insert.
        #   The DB constraint catches both; only one succeeds.
        # FAILURE TEST: No constraint → student submits 3 times → each submission's vectors
        #   match the previous ones → student's own score jumps from 0% to 60%
        #   (self-plagiarism from duplicate rows). Professor sees a 60% score for a student
        #   who copied nobody.
        UniqueConstraint("task_id", "student_id", name="uq_one_submission_per_student"),

        # WHY CheckConstraint?
        #   Float columns accept any float. A bug in scoring could write 150.0 or -5.0.
        #   The UI shows "150% plagiarised" — impossible and confusing.
        #   The DB rejects out-of-range values at write time, not at display time.
        CheckConstraint(
            "overall_similarity_score >= 0.0 AND overall_similarity_score <= 100.0",
            name="ck_score_range",
        ),
    )

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
