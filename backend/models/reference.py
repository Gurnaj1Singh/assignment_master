"""
ReferenceDocument — a professor-uploaded reference PDF for a given task.
ReferenceVector   — SBERT embeddings for each chunk of a reference document.

Design mirrors text_vector.py: ReferenceVector has no TimestampMixin or
SoftDeleteMixin because it is derived, append-only data. Rows are created once
and cascade-deleted with their parent ReferenceDocument.
"""

import uuid

from sqlalchemy import BigInteger, Column, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from .base import Base, SoftDeleteMixin, TimestampMixin

# Reuse the existing DB ENUM — create_type=False prevents Alembic from trying
# to CREATE TYPE again when the migration runs.
reference_chunk_type = Enum(
    "sentence", "paragraph",
    name="text_chunk_type",
    create_type=False,
)


class ReferenceDocument(TimestampMixin, SoftDeleteMixin, Base):
    """
    A professor-uploaded reference/source PDF attached to an assignment task.

    Stored separately from student submissions so the professor can add
    textbooks, papers, or answer keys that the plagiarism engine should
    treat as 'known sources' rather than student work.

    file_path : relative from project root (uploads/references/<uuid>.pdf).
                Relative paths survive server migrations; absolute paths don't.
    """

    __tablename__ = "reference_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("assignment_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(300), nullable=False)
    file_path = Column(String(500), nullable=False)
    uploaded_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    task = relationship("AssignmentTask")
    uploader = relationship("User")
    vectors = relationship(
        "ReferenceVector",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ReferenceDocument title={self.title!r} task={self.task_id}>"


class ReferenceVector(Base):
    """
    SBERT sentence/paragraph embeddings for a reference document chunk.

    No TimestampMixin or SoftDeleteMixin — derived data, same rationale as
    TextVector. Created once during upload processing; deleted via CASCADE.

    type      : 'sentence' — used for source-exclusion matching.
                'paragraph' — reserved for RAG retrieval.
    seq_order : preserves original document order for report rendering.
    """

    __tablename__ = "reference_vectors"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    reference_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reference_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content_chunk = Column(Text, nullable=False)
    embedding = Column(Vector(768), nullable=False)
    type = Column(reference_chunk_type, nullable=False)
    seq_order = Column(Integer, nullable=False)

    __table_args__ = (
        # Fast lookup by reference + type — mirrors ix_tv_submission_type pattern.
        Index("ix_rv_reference_type", "reference_id", "type"),
    )

    document = relationship("ReferenceDocument", back_populates="vectors")

    def __repr__(self) -> str:
        return f"<ReferenceVector id={self.id} type={self.type} order={self.seq_order}>"
