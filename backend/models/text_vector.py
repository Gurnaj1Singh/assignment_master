from sqlalchemy import BigInteger, Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from .base import Base


class TextVector(Base):
    """
    AI-generated semantic embeddings for each sentence/paragraph from a PDF.

    embedding: 768-dimensional vector via SBERT all-mpnet-base-v2
    type: 'sentence' (for scoring) or 'paragraph' (for context)
    seq_order: original document order

    Uses pgvector operator `<=>` for cosine distance.
    Pairs above 0.85 similarity are flagged as plagiarism.
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
    type = Column(String(20), nullable=False)
    seq_order = Column(Integer, nullable=False)

    submission = relationship("Submission", back_populates="vectors")

    def __repr__(self) -> str:
        return f"<TextVector id={self.id} type={self.type} order={self.seq_order}>"
