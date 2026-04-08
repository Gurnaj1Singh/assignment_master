"""
Database Models — Assignment Master
====================================
All SQLAlchemy ORM models are defined here. Each class maps 1:1 to a
PostgreSQL table. Import `Base` into database.py so `Base.metadata.create_all()`
can auto-create every table defined below.

Table overview:
  users                  → everyone who uses the system (professors & students)
  classrooms             → a professor's course
  classroom_memberships  → which students are enrolled in which classroom
  assignment_tasks       → a specific assignment inside a classroom
  submissions            → a student's PDF submission for a task
  text_vectors           → AI sentence embeddings extracted from a submission
"""

from sqlalchemy import (
    BigInteger, Column, DateTime, Float,
    ForeignKey, Integer, String, Text, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid


Base = declarative_base()


# ---------------------------------------------------------------------------
# users
# ---------------------------------------------------------------------------

class User(Base):
    """
    Represents any person using the system.

    role='professor' → can create classrooms, create tasks, view reports.
    role='student'   → can join classrooms, submit assignments.
    """
    __tablename__ = "users"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name          = Column(String(100), nullable=False)
    email         = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    role          = Column(String(20), nullable=False)  # 'professor' | 'student'

    # Relationships — accessible as Python attributes (not extra DB columns)
    memberships = relationship("ClassroomMembership", back_populates="student",
                               cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="student",
                               cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User id={self.id} email={self.email} role={self.role}>"


# ---------------------------------------------------------------------------
# classrooms
# ---------------------------------------------------------------------------

class Classroom(Base):
    """
    A course created by a professor.

    class_code is a random 6-character alphanumeric code that students use
    to enroll (like a Google Classroom join code).
    """
    __tablename__ = "classrooms"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    professor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
                          nullable=False, index=True)
    class_name   = Column(String(200), nullable=False)
    class_code   = Column(String(10), unique=True, nullable=False, index=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    professor   = relationship("User", foreign_keys=[professor_id])
    memberships = relationship("ClassroomMembership", back_populates="classroom",
                               cascade="all, delete-orphan")
    tasks       = relationship("AssignmentTask", back_populates="classroom",
                               cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Classroom name={self.class_name!r} code={self.class_code}>"


# ---------------------------------------------------------------------------
# classroom_memberships  (NEW — the junction table that was missing)
# ---------------------------------------------------------------------------

class ClassroomMembership(Base):
    """
    Junction table that records which students are enrolled in which classroom.

    This solves the many-to-many relationship between users (students) and
    classrooms. Previously this data was not persisted — joining a class had
    no effect in the database.

    Constraints:
      - A student can only be enrolled in a specific classroom once
        (enforced by the UniqueConstraint on classroom_id + student_id).
    """
    __tablename__ = "classroom_memberships"

    id           = Column(BigInteger, primary_key=True, autoincrement=True)
    classroom_id = Column(UUID(as_uuid=True), ForeignKey("classrooms.id", ondelete="CASCADE"),
                          nullable=False, index=True)
    student_id   = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
                          nullable=False, index=True)
    joined_at    = Column(DateTime(timezone=True), server_default=func.now())

    # Prevent a student from joining the same class twice at the DB level
    __table_args__ = (
        UniqueConstraint("classroom_id", "student_id", name="uq_classroom_student"),
    )

    # Relationships (lets you do membership.student.name, membership.classroom.class_name, etc.)
    classroom = relationship("Classroom", back_populates="memberships")
    student   = relationship("User", back_populates="memberships")

    def __repr__(self):
        return (f"<ClassroomMembership classroom={self.classroom_id} "
                f"student={self.student_id}>")


# ---------------------------------------------------------------------------
# assignment_tasks
# ---------------------------------------------------------------------------

class AssignmentTask(Base):
    """
    A specific assignment posted inside a classroom by a professor.

    assignment_code is a unique 6-char code — students use this when
    submitting so the system knows which task a PDF belongs to.
    """
    __tablename__ = "assignment_tasks"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    classroom_id    = Column(UUID(as_uuid=True), ForeignKey("classrooms.id", ondelete="CASCADE"),
                             nullable=False, index=True)
    title           = Column(String(300), nullable=False)
    assignment_code = Column(String(10), unique=True, nullable=False)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    classroom   = relationship("Classroom", back_populates="tasks")
    submissions = relationship("Submission", back_populates="task",
                               cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AssignmentTask title={self.title!r} code={self.assignment_code}>"


# ---------------------------------------------------------------------------
# submissions
# ---------------------------------------------------------------------------

class Submission(Base):
    """
    Tracks a student's PDF submission for a specific assignment task.

    overall_similarity_score is populated AFTER the plagiarism analysis runs.
    It represents what percentage of the student's sentences matched another
    submission (0.0 = clean, 100.0 = fully plagiarised).

    file_path stores the absolute path to the saved PDF on disk.
    """
    __tablename__ = "submissions"

    id                      = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id                 = Column(UUID(as_uuid=True), ForeignKey("assignment_tasks.id", ondelete="CASCADE"),
                                     nullable=False, index=True)
    student_id              = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
                                     nullable=False, index=True)
    overall_similarity_score = Column(Float, default=0.0, nullable=False)
    submitted_at            = Column(DateTime(timezone=True), server_default=func.now())
    file_path               = Column(Text, nullable=False)

    # Relationships
    task    = relationship("AssignmentTask", back_populates="submissions")
    student = relationship("User", back_populates="submissions")
    vectors = relationship("TextVector", back_populates="submission",
                           cascade="all, delete-orphan")

    def __repr__(self):
        return (f"<Submission id={self.id} student={self.student_id} "
                f"score={self.overall_similarity_score}%>")


# ---------------------------------------------------------------------------
# text_vectors
# ---------------------------------------------------------------------------

class TextVector(Base):
    """
    Stores AI-generated semantic embeddings for each sentence/paragraph
    extracted from a student's submission PDF.

    This is the core table that powers plagiarism detection:
      - content_chunk: the raw text (a sentence or paragraph)
      - embedding: a 768-dimensional vector produced by the SBERT model
        (all-mpnet-base-v2). Semantically similar sentences produce vectors
        that are geometrically close — so we can catch paraphrased plagiarism.
      - type: 'sentence' (used for scoring) or 'paragraph' (stored for context)
      - seq_order: original order in the document, used when displaying results

    The pgvector operator `<=>` computes cosine distance between two embeddings.
    Similarity = 1 - cosine_distance. Pairs above 0.85 are flagged.
    """
    __tablename__ = "text_vectors"

    id            = Column(BigInteger, primary_key=True, autoincrement=True)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id", ondelete="CASCADE"),
                           nullable=False, index=True)
    content_chunk = Column(Text, nullable=False)
    embedding     = Column(Vector(768), nullable=False)  # pgvector column
    type          = Column(String(20), nullable=False)   # 'sentence' | 'paragraph'
    seq_order     = Column(Integer, nullable=False)

    # Relationship
    submission = relationship("Submission", back_populates="vectors")

    def __repr__(self):
        return (f"<TextVector id={self.id} type={self.type} "
                f"order={self.seq_order}>")
