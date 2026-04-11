"""
TextVector — stores SBERT sentence embeddings for every submission.

No TimestampMixin or SoftDeleteMixin — these are derived, append-only rows.
They are created once during submission processing and deleted only via CASCADE
when the parent Submission is removed. Adding audit columns would waste storage
across potentially millions of rows with zero business value.
"""

from sqlalchemy import BigInteger, Column, Enum, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from .base import Base

# ---------------------------------------------------------------------------
# ENUM for chunk type.
# WHY ENUM over String(20)?
#   The application only ever writes "sentence" or "paragraph". If a bug writes
#   "Sentence" or "chunk", the vector_repo raw SQL filter `AND v1.type = 'sentence'`
#   silently finds zero rows. The HNSW index is not used. Plagiarism scores are 0%.
#   The ENUM makes the DB enforce the contract so the bug surfaces at write time.
# ---------------------------------------------------------------------------
text_chunk_type = Enum("sentence", "paragraph", name="text_chunk_type")


class TextVector(Base):
    """
    AI-generated semantic embeddings for each sentence/paragraph of a submission.

    embedding : 768-dimensional float vector from SBERT all-mpnet-base-v2.
                The HNSW index on this column enables fast approximate nearest-
                neighbour search using the pgvector `<=>` cosine distance operator.

    type      : 'sentence' — used for plagiarism scoring.
                'paragraph' — reserved for RAG retrieval (Day 3 feature).

    seq_order : preserves original document order for report rendering.
    """

    __tablename__ = "text_vectors"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    submission_id = Column(
        UUID(as_uuid=True),
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content_chunk = Column(Text, nullable=False)
    embedding = Column(Vector(768), nullable=False)
    type = Column(text_chunk_type, nullable=False)
    seq_order = Column(Integer, nullable=False)

    __table_args__ = (
        # WHY this composite index?
        #   Nearly every query filters by BOTH submission_id AND type simultaneously:
        #     WHERE submission_id = :id AND type = 'sentence'
        #   A single-column index on submission_id still scans ALL types for that
        #   submission. A composite index (submission_id, type) lets PostgreSQL jump
        #   directly to the sentence rows, skipping paragraph rows entirely.
        # FAILURE TEST: No composite index, 30 students × 50 sentences + 20 paragraphs
        #   each = 2100 rows per query pass. With 300 students = 21,000 rows scanned
        #   per submission analysis. With the composite index: ~50 rows touched.
        Index("ix_tv_submission_type", "submission_id", "type"),

        # WHY this index?
        #   get_submission_matches() orders results by seq_order for the report view.
        #   Without this index, PostgreSQL sorts all matching rows in memory (filesort).
        #   With the index, rows arrive pre-sorted from storage — O(1) sort cost.
        Index("ix_tv_submission_order", "submission_id", "seq_order"),
    )

    submission = relationship("Submission", back_populates="vectors")

    def __repr__(self) -> str:
        return f"<TextVector id={self.id} type={self.type} order={self.seq_order}>"
