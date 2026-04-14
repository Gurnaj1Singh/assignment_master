"""Core plagiarism detection — embedding, comparison, scoring."""

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy.orm import Session

from ..config import settings
from ..repositories.reference_repo import ReferenceVectorRepository
from ..repositories.submission_repo import SubmissionRepository
from ..repositories.vector_repo import VectorRepository
from .nlp_service import NLPService
from .text_utils import is_verbatim


@dataclass
class ScoringResult:
    """Holds plagiarism scoring output including source-exclusion details."""

    score: float
    match_details: list
    verbatim_flag: bool = False
    verbatim_matches: list = field(default_factory=list)


class PlagiarismService:
    def __init__(self, db: Session, nlp: NLPService):
        self.db = db
        self.nlp = nlp
        self.vector_repo = VectorRepository(db)
        self.submission_repo = SubmissionRepository(db)
        self.ref_vector_repo = ReferenceVectorRepository(db)
        self.threshold = settings.SIMILARITY_THRESHOLD

    def process_submission(
        self, text_content: str, submission_id: UUID, task_id: UUID
    ) -> ScoringResult:
        """
        Full pipeline: chunk -> embed -> store -> score.
        Returns a ScoringResult with score, matches, sentence_count, and verbatim info.
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

        # Build a lookup from sentence text -> embedding for reference checks
        sentence_embeddings = dict(zip(sentences, embeddings))

        result = self._calculate_score(
            submission_id, task_id, sentence_embeddings
        )
        result.sentence_count = len(sentences)
        return result

    def _calculate_score(
        self,
        submission_id: UUID,
        task_id: UUID,
        sentence_embeddings: dict[str, list[float]],
    ) -> ScoringResult:
        # Step 1: Find all inter-student matches (unchanged query)
        results = self.vector_repo.find_similar_vectors(
            submission_id, task_id, threshold=self.threshold
        )
        total = self.vector_repo.count_vectors(
            submission_id, vec_type="sentence"
        )

        if total == 0:
            return ScoringResult(score=0.0, match_details=[])

        # Step 2: Source exclusion — for each flagged student sentence,
        # check if it also matches the reference corpus.
        flagged_sentences = {r.student_sentence for r in results}
        excluded_sentences: set[str] = set()
        verbatim_matches: list[dict] = []

        for sentence in flagged_sentences:
            embedding = sentence_embeddings.get(sentence)
            if embedding is None:
                continue

            ref_matches = self.ref_vector_repo.find_matching_reference(
                embedding, task_id, threshold=self.threshold
            )

            if not ref_matches:
                # No reference match — this is inter-student plagiarism
                continue

            # Reference match found — check for verbatim copying
            best_ref = ref_matches[0]  # highest similarity
            if is_verbatim(sentence, best_ref.reference_chunk):
                # Verbatim copy of reference — flag it, don't exclude
                verbatim_matches.append({
                    "student_sentence": sentence,
                    "reference_sentence": best_ref.reference_chunk,
                    "similarity_score": round(float(best_ref.similarity_score), 4),
                    "is_verbatim": True,
                })
            else:
                # Paraphrased from reference — exclude from plagiarism score
                excluded_sentences.add(sentence)

        # Step 3: Recalculate score excluding reference-paraphrased sentences
        plagiarism_sentences = flagged_sentences - excluded_sentences
        flagged_count = len(plagiarism_sentences)
        score = round((flagged_count / total) * 100, 2)

        return ScoringResult(
            score=score,
            match_details=results,
            verbatim_flag=len(verbatim_matches) > 0,
            verbatim_matches=verbatim_matches,
        )
