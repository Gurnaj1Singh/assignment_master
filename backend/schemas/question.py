"""Pydantic V2 schemas for LLM question generation and distribution."""

from uuid import UUID

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    """Optional parameters for question generation."""
    count: int = Field(default=100, ge=1, le=200)
    provider: str | None = Field(
        default=None,
        description="LLM provider: 'openai' or 'ollama'. Defaults to server config.",
    )


class QuestionResponse(BaseModel):
    """Single generated question."""
    question_id: UUID
    question_text: str
    difficulty: str
    bloom_level: str
    is_selected: bool

    model_config = {"from_attributes": True}


class SelectQuestionsRequest(BaseModel):
    """Professor selects which questions to use."""
    question_ids: list[UUID]


class DistributeRequest(BaseModel):
    """Professor distributes Y questions per student."""
    num_per_student: int = Field(..., ge=1)


class StudentAssignmentItem(BaseModel):
    student_id: str
    question_id: str


class DistributionResponse(BaseModel):
    """Summary of question distribution."""
    total_students: int
    questions_per_student: int
    total_assignments: int
    assignments: list[StudentAssignmentItem]


class StudentQuestionResponse(BaseModel):
    """A question as seen by a student."""
    question_id: UUID
    question_text: str
    difficulty: str

    model_config = {"from_attributes": True}
