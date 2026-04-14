"""
LLM-powered question generation service using RAG.

Retrieves all reference paragraph chunks for a task, feeds them as context
to GPT, and parses the structured JSON output into GeneratedQuestion records.
"""

import json
import logging
from uuid import UUID

from fastapi import HTTPException, status
from openai import OpenAI, APIConnectionError, RateLimitError, APITimeoutError
from sqlalchemy.orm import Session

from ..config import settings
from ..models.question import GeneratedQuestion
from ..repositories.question_repo import QuestionRepository
from ..repositories.reference_repo import (
    ReferenceDocumentRepository,
    ReferenceVectorRepository,
)
from ..services.nlp_service import NLPService

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self, db: Session):
        self.db = db
        self.question_repo = QuestionRepository(db)
        self.ref_doc_repo = ReferenceDocumentRepository(db)
        self.ref_vec_repo = ReferenceVectorRepository(db)
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate_questions(
        self,
        task_id: UUID,
        nlp_service: NLPService,
    ) -> list[GeneratedQuestion]:
        """
        Generate 100 diverse questions from reference material using RAG.

        1. Retrieve ALL paragraph-level reference vectors for the task.
        2. Build a prompt with the reference context.
        3. Call OpenAI to generate questions in JSON format.
        4. Parse and store all questions in the database.
        """
        # Retrieve all paragraph chunks for this task
        context_chunks = self._get_reference_paragraphs(task_id)
        if not context_chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No reference documents found for this task. "
                       "Upload reference PDFs before generating questions.",
            )

        # Build the prompt and call the LLM
        system_prompt, user_prompt = self._build_question_prompt(context_chunks)

        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.8,
                max_tokens=16000,
            )
        except RateLimitError:
            logger.error("OpenAI rate limit hit during question generation")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="LLM rate limit reached. Please try again in a few minutes.",
            )
        except APITimeoutError:
            logger.error("OpenAI API timeout during question generation")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="LLM request timed out. Please try again.",
            )
        except APIConnectionError:
            logger.error("OpenAI API connection error during question generation")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Could not connect to LLM service. Please try again later.",
            )

        # Parse the JSON response
        raw_content = response.choices[0].message.content
        questions_data = self._parse_llm_response(raw_content)

        # Store all questions
        question_dicts = [
            {
                "task_id": task_id,
                "question_text": q["question_text"],
                "difficulty": q["difficulty"],
                "bloom_level": q["bloom_level"],
            }
            for q in questions_data
        ]
        created = self.question_repo.bulk_create(question_dicts)
        self.db.commit()

        # Refresh to get generated IDs
        for q in created:
            self.db.refresh(q)

        logger.info(
            "Generated %d questions for task %s", len(created), task_id
        )
        return created

    def _get_reference_paragraphs(self, task_id: UUID) -> list[str]:
        """Retrieve all paragraph text chunks from reference vectors for this task."""
        from sqlalchemy import text

        query = text("""
            SELECT rv.content_chunk
            FROM reference_vectors rv
            JOIN reference_documents rd ON rv.reference_id = rd.id
            WHERE rd.task_id = :task_id
              AND rd.is_deleted = false
              AND rv.type = 'paragraph'
            ORDER BY rd.created_at ASC, rv.seq_order ASC
        """)
        rows = self.db.execute(query, {"task_id": task_id}).all()
        return [row[0] for row in rows]

    def _build_question_prompt(
        self, context_chunks: list[str]
    ) -> tuple[str, str]:
        """Build the system and user prompts for question generation."""
        numbered_context = "\n\n".join(
            f"[Paragraph {i+1}]\n{chunk}"
            for i, chunk in enumerate(context_chunks)
        )

        system_prompt = (
            "You are an expert academic question generator. Your task is to create "
            "diverse, high-quality questions based on provided reference material. "
            "Generate questions that span all six levels of Bloom's taxonomy: "
            "Remember, Understand, Apply, Analyze, Evaluate, and Create. "
            "Each question should have a difficulty level (easy, medium, or hard) "
            "and a Bloom's taxonomy level.\n\n"
            "You MUST respond with valid JSON in exactly this format:\n"
            '{"questions": [\n'
            '  {"question_text": "...", "difficulty": "easy|medium|hard", '
            '"bloom_level": "Remember|Understand|Apply|Analyze|Evaluate|Create"},\n'
            "  ...\n"
            "]}\n\n"
            "Rules:\n"
            "- Generate exactly 100 questions\n"
            "- Distribute questions roughly evenly across all 6 Bloom's levels\n"
            "- Mix difficulty levels: ~30 easy, ~40 medium, ~30 hard\n"
            "- Questions must be directly based on the provided reference material\n"
            "- Each question should be self-contained and unambiguous\n"
            "- Avoid duplicate or near-duplicate questions\n"
            "- difficulty must be exactly one of: easy, medium, hard\n"
            "- bloom_level must be exactly one of: Remember, Understand, Apply, "
            "Analyze, Evaluate, Create"
        )

        user_prompt = (
            "Based on the following reference material, generate 100 diverse "
            "academic questions.\n\n"
            f"--- REFERENCE MATERIAL ---\n\n{numbered_context}\n\n"
            "--- END REFERENCE MATERIAL ---\n\n"
            "Generate exactly 100 questions covering all Bloom's taxonomy levels "
            "and difficulty levels. Respond ONLY with the JSON object."
        )

        return system_prompt, user_prompt

    def _parse_llm_response(self, raw_content: str) -> list[dict]:
        """Parse the LLM JSON response into a list of question dicts."""
        try:
            data = json.loads(raw_content)
        except json.JSONDecodeError:
            logger.error("Failed to parse LLM response as JSON: %s", raw_content[:500])
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to parse LLM response. Please try again.",
            )

        questions = data.get("questions", [])
        if not questions:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="LLM returned no questions. Please try again.",
            )

        valid_difficulties = {"easy", "medium", "hard"}
        valid_blooms = {"Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"}

        parsed = []
        for q in questions:
            text = q.get("question_text", "").strip()
            difficulty = q.get("difficulty", "medium").lower()
            bloom = q.get("bloom_level", "Remember")

            if not text:
                continue
            if difficulty not in valid_difficulties:
                difficulty = "medium"
            if bloom not in valid_blooms:
                bloom = "Remember"

            parsed.append({
                "question_text": text,
                "difficulty": difficulty,
                "bloom_level": bloom,
            })

        if not parsed:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="LLM response contained no valid questions. Please try again.",
            )

        return parsed
