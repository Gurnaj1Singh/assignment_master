"""
LLM question generation and distribution API routes.

All endpoints are synchronous (def, not async def) — OpenAI API calls and
DB operations run in FastAPI's threadpool and do not block the event loop.
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.user import User
from ...schemas.question import (
    DistributeRequest,
    DistributionResponse,
    GenerateRequest,
    QuestionResponse,
    SelectQuestionsRequest,
    StudentQuestionResponse,
)
from ...services.llm_service import LLMService
from ...services.nlp_service import NLPService, get_nlp_service
from ...services.question_distribution_service import QuestionDistributionService
from ..deps import get_current_user, require_role

router = APIRouter()


@router.post("/generate/{task_id}", response_model=list[QuestionResponse], status_code=201)
def generate_questions(
    task_id: UUID,
    body: GenerateRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    nlp: NLPService = Depends(get_nlp_service),
):
    """
    Professor triggers LLM question generation from reference material.

    Retrieves all paragraph embeddings for the task's reference corpus,
    builds a RAG prompt, and generates 100 diverse deep-thinking questions.

    Accepts optional JSON body with `provider` ("openai" or "ollama")
    to override the server default.
    """
    require_role(current_user, "professor", "Only professors can generate questions.")

    # Ownership check is done inside the service via task → classroom → professor
    service = QuestionDistributionService(db)
    service._validate_task_ownership(task_id, current_user.id)

    provider = body.provider if body else None

    llm = LLMService(db)
    questions = llm.generate_questions(task_id=task_id, nlp_service=nlp, provider=provider)

    return [
        QuestionResponse(
            question_id=q.id,
            question_text=q.question_text,
            difficulty=q.difficulty,
            bloom_level=q.bloom_level,
            is_selected=q.is_selected,
        )
        for q in questions
    ]


@router.get("/list/{task_id}", response_model=list[QuestionResponse])
def list_questions(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Professor views all generated questions for a task."""
    require_role(current_user, "professor", "Only professors can view generated questions.")

    service = QuestionDistributionService(db)
    service._validate_task_ownership(task_id, current_user.id)

    from ...repositories.question_repo import QuestionRepository
    questions = QuestionRepository(db).get_by_task(task_id)

    return [
        QuestionResponse(
            question_id=q.id,
            question_text=q.question_text,
            difficulty=q.difficulty,
            bloom_level=q.bloom_level,
            is_selected=q.is_selected,
        )
        for q in questions
    ]


@router.post("/select/{task_id}", status_code=200)
def select_questions(
    task_id: UUID,
    body: SelectQuestionsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Professor selects X questions from the generated pool."""
    require_role(current_user, "professor", "Only professors can select questions.")

    service = QuestionDistributionService(db)
    count = service.select_questions(
        task_id=task_id,
        question_ids=body.question_ids,
        professor_id=current_user.id,
    )
    return {"message": f"{count} questions selected successfully."}


@router.post("/distribute/{task_id}", response_model=DistributionResponse, status_code=201)
def distribute_questions(
    task_id: UUID,
    body: DistributeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Professor distributes Y questions per student from selected pool."""
    require_role(current_user, "professor", "Only professors can distribute questions.")

    service = QuestionDistributionService(db)
    result = service.distribute_questions(
        task_id=task_id,
        num_per_student=body.num_per_student,
        professor_id=current_user.id,
    )
    return DistributionResponse(**result)


@router.get("/my-questions/{task_id}", response_model=list[StudentQuestionResponse])
def get_my_questions(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Student views their assigned questions for a task."""
    require_role(current_user, "student", "Only students can view their assigned questions.")

    from ...repositories.question_repo import StudentQuestionRepo
    repo = StudentQuestionRepo(db)
    assignments = repo.get_for_student(
        student_id=current_user.id,
        task_id=task_id,
    )

    return [
        StudentQuestionResponse(
            question_id=a.question.id,
            question_text=a.question.question_text,
            difficulty=a.question.difficulty,
        )
        for a in assignments
    ]
