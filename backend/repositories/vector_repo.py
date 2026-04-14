"""pgvector-specific queries for semantic similarity."""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..models.text_vector import TextVector


class VectorRepository:
    def __init__(self, db: Session):
        self.db = db

    def bulk_create(
        self,
        submission_id: UUID,
        sentences: list[str],
        embeddings: list[list[float]],
        vec_type: str = "sentence",
    ) -> None:
        for i, (chunk, embedding) in enumerate(zip(sentences, embeddings)):
            self.db.add(
                TextVector(
                    submission_id=submission_id,
                    content_chunk=chunk,
                    embedding=embedding,
                    type=vec_type,
                    seq_order=i,
                )
            )
        self.db.flush()

    def count_vectors(self, submission_id: UUID, vec_type: str = "sentence") -> int:
        q = text(
            "SELECT count(*) FROM text_vectors "
            "WHERE submission_id = :sub_id AND type = :vec_type"
        )
        return self.db.execute(
            q, {"sub_id": submission_id, "vec_type": vec_type}
        ).scalar()

    def find_similar_vectors(
        self,
        submission_id: UUID,
        task_id: UUID,
        threshold: float = 0.85,
    ) -> list:
        query = text("""
            SELECT
                v1.content_chunk AS student_sentence,
                v2.content_chunk AS matched_sentence,
                u.name           AS matched_student_name,
                1 - (v1.embedding <=> v2.embedding) AS similarity_score
            FROM text_vectors v1
            JOIN text_vectors v2 ON v1.submission_id != v2.submission_id
            JOIN submissions  s  ON v2.submission_id = s.id
            JOIN users        u  ON s.student_id    = u.id
            WHERE v1.submission_id = :sub_id
              AND s.task_id        = :task_id
              AND s.is_deleted     = false
              AND v1.type          = 'sentence'
              AND (1 - (v1.embedding <=> v2.embedding)) > :threshold
        """)
        return self.db.execute(
            query,
            {"sub_id": submission_id, "task_id": task_id, "threshold": threshold},
        ).all()

    def get_submission_matches(
        self, submission_id: UUID, threshold: float = 0.85
    ) -> list:
        query = text("""
            SELECT
                v1.content_chunk AS student_text,
                v2.content_chunk AS matched_text,
                u_source.name    AS copied_from,
                1 - (v1.embedding <=> v2.embedding) AS similarity
            FROM text_vectors v1
            JOIN text_vectors v2  ON v1.submission_id != v2.submission_id
            JOIN submissions  s_source ON v2.submission_id = s_source.id
            JOIN users        u_source ON s_source.student_id = u_source.id
            WHERE v1.submission_id = :sub_id
              AND s_source.is_deleted = false
              AND (1 - (v1.embedding <=> v2.embedding)) > :threshold
            ORDER BY v1.seq_order ASC
        """)
        return self.db.execute(
            query, {"sub_id": submission_id, "threshold": threshold}
        ).all()

    def get_similarity_matrix(self, task_id: UUID, threshold: float = 0.85) -> list:
        query = text("""
            SELECT
                u1.name   AS student_a,
                u2.name   AS student_b,
                AVG(1 - (v1.embedding <=> v2.embedding)) AS avg_similarity,
                COUNT(*) FILTER (
                    WHERE (1 - (v1.embedding <=> v2.embedding)) > :threshold
                ) AS matching_sentences
            FROM text_vectors v1
            JOIN text_vectors v2 ON v1.submission_id != v2.submission_id
            JOIN submissions  s1 ON v1.submission_id = s1.id
            JOIN submissions  s2 ON v2.submission_id = s2.id
            JOIN users        u1 ON s1.student_id    = u1.id
            JOIN users        u2 ON s2.student_id    = u2.id
            WHERE s1.task_id  = :task_id
              AND s2.task_id  = :task_id
              AND s1.id < s2.id
              AND s1.is_deleted = false
              AND s2.is_deleted = false
              AND v1.type = 'sentence'
              AND v2.type = 'sentence'
            GROUP BY u1.name, u2.name
            HAVING COUNT(*) FILTER (
                WHERE (1 - (v1.embedding <=> v2.embedding)) > :threshold
            ) > 5
        """)
        return self.db.execute(
            query, {"task_id": task_id, "threshold": threshold}
        ).all()

    def get_heatmap_data(self, task_id: UUID, threshold: float = 0.85) -> list:
        """
        Pairwise similarity for ALL student pairs in a task.
        Returns every pair regardless of similarity level (frontend renders the heatmap).

        NOTE: This is O(n^2) in student count × sentence count. For large classes
        (50+ students with 100+ sentences each), consider caching the result with
        a TTL of ~5 minutes keyed on (task_id, last_submission_timestamp).
        """
        query = text("""
            WITH sentence_counts AS (
                SELECT s.student_id, COUNT(*) AS total_sentences
                FROM text_vectors v
                JOIN submissions s ON v.submission_id = s.id
                WHERE s.task_id = :task_id
                  AND s.is_deleted = false
                  AND v.type = 'sentence'
                GROUP BY s.student_id
            )
            SELECT
                u1.name AS student_a,
                u2.name AS student_b,
                AVG(1 - (v1.embedding <=> v2.embedding)) * 100 AS similarity,
                COUNT(*) FILTER (
                    WHERE (1 - (v1.embedding <=> v2.embedding)) > :threshold
                ) AS shared_sentences,
                sc1.total_sentences AS total_sentences_a,
                sc2.total_sentences AS total_sentences_b
            FROM text_vectors v1
            JOIN text_vectors v2 ON v1.submission_id != v2.submission_id
            JOIN submissions  s1 ON v1.submission_id = s1.id
            JOIN submissions  s2 ON v2.submission_id = s2.id
            JOIN users        u1 ON s1.student_id    = u1.id
            JOIN users        u2 ON s2.student_id    = u2.id
            JOIN sentence_counts sc1 ON s1.student_id = sc1.student_id
            JOIN sentence_counts sc2 ON s2.student_id = sc2.student_id
            WHERE s1.task_id  = :task_id
              AND s2.task_id  = :task_id
              AND s1.id < s2.id
              AND s1.is_deleted = false
              AND s2.is_deleted = false
              AND v1.type = 'sentence'
              AND v2.type = 'sentence'
            GROUP BY u1.name, u2.name, sc1.total_sentences, sc2.total_sentences
        """)
        return self.db.execute(
            query, {"task_id": task_id, "threshold": threshold}
        ).all()

    def get_collusion_pairs(self, task_id: UUID) -> list:
        """
        Returns student name pairs where pairwise similarity
        exceeds 30% (based on shared high-similarity vectors).
        """
        query = text("""
            WITH pairwise AS (
                SELECT
                    s1.student_id AS sid1,
                    s2.student_id AS sid2,
                    COUNT(*) FILTER (
                        WHERE (1 - (v1.embedding <=> v2.embedding)) > 0.85
                    ) AS shared_flagged,
                    COUNT(*) AS total_compared
                FROM text_vectors v1
                JOIN text_vectors v2 ON v1.submission_id != v2.submission_id
                JOIN submissions s1  ON v1.submission_id = s1.id
                JOIN submissions s2  ON v2.submission_id = s2.id
                WHERE s1.task_id = :task_id
                  AND s2.task_id = :task_id
                  AND s1.id < s2.id
                  AND s1.is_deleted = false
                  AND s2.is_deleted = false
                  AND v1.type = 'sentence'
                  AND v2.type = 'sentence'
                GROUP BY s1.student_id, s2.student_id
            )
            SELECT u1.name, u2.name
            FROM pairwise p
            JOIN users u1 ON p.sid1 = u1.id
            JOIN users u2 ON p.sid2 = u2.id
            WHERE (p.shared_flagged::float / NULLIF(p.total_compared, 0)) > 0.30
        """)
        return self.db.execute(query, {"task_id": task_id}).all()
