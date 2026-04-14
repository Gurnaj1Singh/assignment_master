"""Classroom and task request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ClassroomCreateRequest(BaseModel):
    class_name: str = Field(
        ..., min_length=2, max_length=200,
        description="Human-readable name, e.g. 'Robotics & AI'",
    )


class ClassroomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    class_id: UUID
    class_name: str
    class_code: str
    created_at: datetime | None = None
    joined_at: datetime | None = None
    student_count: int | None = None


class StudentInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    student_id: UUID
    name: str
    email: str
    joined_at: datetime | None = None


class ClassroomMemberResponse(BaseModel):
    class_name: str
    class_code: str
    total_students: int
    students: list[StudentInfo]


class TaskCreateRequest(BaseModel):
    title: str = Field(
        ..., min_length=2, max_length=300,
        description="Assignment title, e.g. 'NLP Research Paper'",
    )
    description: str | None = Field(
        default=None,
        description="Optional instructions or rubric visible to students.",
    )
    due_date: datetime | None = Field(
        default=None,
        description="Assignment deadline (timezone-aware ISO 8601). None = no cutoff.",
        examples=["2026-05-20T23:59:59+05:30"],
    )


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message: str
    task_id: UUID
    task_code: str
    title: str


class TaskDetailResponse(BaseModel):
    """Full task detail — returned after PDF upload or when listing tasks."""
    model_config = ConfigDict(from_attributes=True)

    task_id: UUID
    title: str
    description: str | None
    assignment_code: str
    due_date: datetime | None
    is_published: bool
    has_pdf: bool          # True if professor has uploaded a question paper
    created_at: datetime


class TaskListEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: UUID
    title: str
    description: str | None
    assignment_code: str
    due_date: datetime | None
    is_published: bool
    has_pdf: bool
    submission_count: int
    created_at: datetime


class TaskDetailFullResponse(BaseModel):
    """Task detail with submission stats. Professor vs student view differs at API layer."""
    model_config = ConfigDict(from_attributes=True)

    task_id: UUID
    title: str
    description: str | None
    assignment_code: str
    due_date: datetime | None
    is_published: bool
    has_pdf: bool
    created_at: datetime
    # Professor-only fields (None for students)
    submission_count: int | None = None
    average_score: float | None = None
    # Student-only fields (None for professors)
    my_status: str | None = None
    my_score: float | None = None
