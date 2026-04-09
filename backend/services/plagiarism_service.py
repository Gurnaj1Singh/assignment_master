"""Core plagiarism detection — embedding, comparison, scoring."""

from uuid import UUID

from sqlalchemy.orm import Session

from ..config import settings
from ..repositories.submission_repo import SubmissionRepository
from ..repositories.vector_repo import VectorRepository
from .nlp_service import NLPService


class PlagiarismService:
    def __init__(self, db: Session, nlp: NLPService):
        self.db = db
        self.nlp = nlp
        self.vector_repo = VectorRepository(db)
        self.submission_repo = SubmissionRepository(db)
        self.threshold = settings.SIMILARITY_THRESHOLD

    def process_submission(
        self, text_content: str, submission_id: UUID, task_id: UUID
    ) -> tuple[float, list, int]:
        """
        Full pipeline: chunk -> embed -> store -> score.
        Returns (score, match_details, sentence_count).
        """
        _, sentences = self.nlp.get_chunks(text_content)
        if not sentences:
            raise ValueError("No readable sentences found in assignment")

        embeddings = self.nlp.generate_embeddings(sentences)

        self.vector_repo.bulk_create(
            submission_id=submission_id,
            sentences=sentences,
            embeddings=embeddings,
            vec_type="sentence",
        )

        score, details = self._calculate_score(submission_id, task_id)
        return score, details, len(sentences)

    def _calculate_score(
        self, submission_id: UUID, task_id: UUID
    ) -> tuple[float, list]:
        results = self.vector_repo.find_similar_vectors(
            submission_id, task_id, threshold=self.threshold
        )
        total = self.vector_repo.count_vectors(
            submission_id, vec_type="sentence"
        )

        if total == 0:
            return 0.0, []

        flagged = len({r.student_sentence for r in results})
        score = round((flagged / total) * 100, 2)
        return score, results
