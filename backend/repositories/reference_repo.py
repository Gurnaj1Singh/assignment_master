"""Repositories for reference corpus models."""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..models.reference import ReferenceDocument, ReferenceVector
from .base import BaseRepository


class ReferenceDocumentRepository(BaseRepository[ReferenceDocument]):
    def __init__(self, db: Session):
        super().__init__(ReferenceDocument, db)

    def get_by_task(self, task_id: UUID) -> list[ReferenceDocument]:
        """Return all non-deleted reference documents for a given task."""
        return (
            self._base_query()
            .filter(ReferenceDocument.task_id == task_id)
            .order_by(ReferenceDocument.created_at.asc())
            .all()
        )


class ReferenceVectorRepository:
    def __init__(self, db: Session):
        self.db = db

    def bulk_create(
        self,
        reference_id: UUID,
        chunks: list[str],
        embeddings: list[list[float]],
        vec_type: str,
    ) -> None:
        """Insert a batch of reference chunk embeddings. Flushes, does not commit."""
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            self.db.add(
                ReferenceVector(
                    reference_id=reference_id,
                    content_chunk=chunk,
                    embedding=embedding,
                    type=vec_type,
                    seq_order=i,
                )
            )
        self.db.flush()

    def find_similar_to_sentence(
        self,
        sentence_embedding: list[float],
        task_id: UUID,
        threshold: float = 0.85,
    ) -> list:
        """
        Return reference chunks whose cosine similarity to the given sentence
        embedding exceeds the threshold.

        Used for source-exclusion matching: if a student's sentence is very
        similar to a known reference document, it should not be counted as
        inter-student plagiarism.
        """
        query = text("""
            SELECT
                rv.content_chunk AS reference_chunk,
                rd.title         AS reference_title,
                1 - (rv.embedding <=> CAST(:embedding AS vector)) AS similarity_score
            FROM reference_vectors rv
            JOIN reference_documents rd ON rv.reference_id = rd.id
            JOIN assignment_tasks    at ON rd.task_id      = at.id
            WHERE at.id            = :task_id
              AND rd.is_deleted    = false
              AND rv.type          = 'sentence'
              AND (1 - (rv.embedding <=> CAST(:embedding AS vector))) > :threshold
            ORDER BY similarity_score DESC
        """)
        return self.db.execute(
            query,
            {
                "embedding": str(sentence_embedding),
                "task_id": task_id,
                "threshold": threshold,
            },
        ).all()
