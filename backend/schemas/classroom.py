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


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message: str
    task_id: UUID
    task_code: str
    title: str
