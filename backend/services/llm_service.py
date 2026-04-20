"""
LLM-powered question generation service using RAG.

Retrieves all reference paragraph chunks for a task, feeds them as context
to the configured LLM provider (OpenAI or Ollama), and parses the structured
JSON output into GeneratedQuestion records.

Supports provider switching via LLM_PROVIDER setting or per-request override.
"""

import json
import logging
from uuid import UUID

from fastapi import HTTPException, status
from openai import (
    OpenAI,
    APIConnectionError,
    AuthenticationError,
    RateLimitError,
    APITimeoutError,
)
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


def _build_client(provider: str) -> tuple[OpenAI, str]:
    """
    Return an OpenAI-compatible client and model name for the given provider.

    Ollama exposes an OpenAI-compatible API at /v1, so we reuse the same SDK
    with a different base_url — no extra dependencies required.
    """
    if provider == "ollama":
        client = OpenAI(
            base_url=settings.OLLAMA_BASE_URL,
            api_key="ollama",  # Ollama ignores this but the SDK requires it
            timeout=600.0,     # Local inference needs more time for 100 questions
        )
        return client, settings.OLLAMA_MODEL
    else:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        return client, settings.OPENAI_MODEL


class LLMService:
    def __init__(self, db: Session):
        self.db = db
        self.question_repo = QuestionRepository(db)
        self.ref_doc_repo = ReferenceDocumentRepository(db)
        self.ref_vec_repo = ReferenceVectorRepository(db)

    def generate_questions(
        self,
        task_id: UUID,
        nlp_service: NLPService,
        provider: str | None = None,
    ) -> list[GeneratedQuestion]:
        """
        Generate 100 diverse deep-thinking questions from reference material.

        1. Retrieve ALL paragraph-level reference vectors for the task.
        2. Build a prompt with the reference context.
        3. Call the LLM (OpenAI or Ollama) to generate questions in JSON format.
        4. Parse and store all questions in the database.

        Args:
            provider: "openai" or "ollama". Falls back to settings.LLM_PROVIDER.
        """
        provider = (provider or settings.LLM_PROVIDER).lower().strip()
        if provider not in ("openai", "ollama"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown LLM provider '{provider}'. Use 'openai' or 'ollama'.",
            )

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
        client, model = _build_client(provider)

        try:
            create_kwargs = dict(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.8,
                max_tokens=16000,
            )
            # OpenAI supports response_format; Ollama support varies by model
            if provider == "openai":
                create_kwargs["response_format"] = {"type": "json_object"}

            response = client.chat.completions.create(**create_kwargs)

        except RateLimitError:
            logger.error("LLM rate limit hit during question generation (provider=%s)", provider)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="LLM rate limit reached. Please try again in a few minutes.",
            )
        except APITimeoutError:
            logger.error("LLM API timeout during question generation (provider=%s)", provider)
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="LLM request timed out. Please try again.",
            )
        except AuthenticationError:
            logger.error("LLM API key is invalid or missing (provider=%s)", provider)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LLM service is not configured. Check your API key.",
            )
        except APIConnectionError:
            if provider == "ollama":
                detail = (
                    "Could not connect to Ollama. "
                    "Make sure Ollama is running (ollama serve) and the model is pulled."
                )
            else:
                detail = "Could not connect to LLM service. Please try again later."
            logger.error("LLM API connection error (provider=%s)", provider)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=detail,
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
            "Generated %d questions for task %s (provider=%s, model=%s)",
            len(created), task_id, provider, model,
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
        """Build the system and user prompts for deep-thinking question generation."""
        numbered_context = "\n\n".join(
            f"[Paragraph {i+1}]\n{chunk}"
            for i, chunk in enumerate(context_chunks)
        )

        system_prompt = (
            "You are an expert academic question designer who creates questions "
            "that provoke deep, critical thinking. Your questions must go beyond "
            "surface-level factual recall and instead challenge students to truly "
            "engage with the material through analysis, reasoning, and synthesis.\n\n"
            "QUESTION DESIGN PRINCIPLES:\n"
            "- Focus on WHY (causes, reasons, motivations, justifications)\n"
            "- Focus on HOW (mechanisms, processes, methods, approaches)\n"
            "- Focus on WHAT-IF (implications, consequences, alternative scenarios)\n"
            "- Require students to COMPARE, CONTRAST, and EVALUATE concepts\n"
            "- Ask students to APPLY concepts to novel situations\n"
            "- Challenge students to SYNTHESIZE ideas across different paragraphs\n"
            "- Pose questions that have no single obvious answer and require argument\n"
            "- Avoid questions answerable with a single fact, name, date, or definition\n\n"
            "Generate questions that span all six levels of Bloom's taxonomy: "
            "Remember, Understand, Apply, Analyze, Evaluate, and Create. "
            "Even 'Remember' level questions should require thoughtful recall of "
            "relationships and processes, not trivial facts.\n\n"
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
            "- Questions must be directly grounded in the provided reference material\n"
            "- Each question should be self-contained and unambiguous\n"
            "- Avoid duplicate or near-duplicate questions\n"
            "- difficulty must be exactly one of: easy, medium, hard\n"
            "- bloom_level must be exactly one of: Remember, Understand, Apply, "
            "Analyze, Evaluate, Create\n"
            "- Do NOT include any text outside the JSON object\n"
            "- Do NOT wrap the JSON in markdown code fences"
        )

        user_prompt = (
            "Based on the following reference material, generate 100 diverse "
            "deep-thinking academic questions that challenge students to reason "
            "about WHY things work the way they do, HOW processes and concepts "
            "interconnect, and WHAT would happen under different conditions.\n\n"
            f"--- REFERENCE MATERIAL ---\n\n{numbered_context}\n\n"
            "--- END REFERENCE MATERIAL ---\n\n"
            "Generate exactly 100 questions covering all Bloom's taxonomy levels "
            "and difficulty levels. Every question should require genuine thought — "
            "not just lookup. Respond ONLY with the JSON object."
        )

        return system_prompt, user_prompt

    @staticmethod
    def _extract_json(raw: str) -> str:
        """Extract the JSON object from raw LLM output.

        Handles common quirks from local models:
        - <think>…</think> reasoning blocks (qwen3/3.5)
        - Markdown code fences (```json … ```)
        - Leading/trailing prose around the JSON
        """
        import re

        # Strip <think>…</think> blocks (qwen3 family)
        cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

        # Strip markdown code fences
        if cleaned.startswith("```"):
            first_newline = cleaned.index("\n")
            cleaned = cleaned[first_newline + 1:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].rstrip()

        # If still not starting with '{', find the first '{' and last '}'
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start:end + 1]

        return cleaned

    def _parse_llm_response(self, raw_content: str) -> list[dict]:
        """Parse the LLM JSON response into a list of question dicts."""
        cleaned = self._extract_json(raw_content)

        try:
            data = json.loads(cleaned)
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

        # Normalise bloom levels: model may return lowercase
        bloom_map = {b.lower(): b for b in valid_blooms}

        parsed = []
        for q in questions:
            # Accept "question_text", "question", or "text" as the key
            text = (
                q.get("question_text")
                or q.get("question")
                or q.get("text")
                or ""
            ).strip()
            difficulty = q.get("difficulty", "medium").lower()
            bloom = q.get("bloom_level") or q.get("bloom") or "Remember"

            if not text:
                continue
            if difficulty not in valid_difficulties:
                difficulty = "medium"
            # Normalise bloom level (accept any casing)
            bloom = bloom_map.get(bloom.lower(), "Remember")

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
