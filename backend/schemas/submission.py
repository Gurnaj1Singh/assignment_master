"""Submission and plagiarism response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class VerbatimMatch(BaseModel):
    """A sentence flagged as verbatim copying from the reference corpus."""

    model_config = ConfigDict(from_attributes=True)

    student_sentence: str
    reference_sentence: str
    similarity_score: float
    is_verbatim: bool


class SubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message: str
    submission_id: UUID
    plagiarism_score: str
    matches_found: int
    sentences_processed: int
    verbatim_flag: bool = False
    verbatim_matches: list[VerbatimMatch] = []


class PlagiarismMatch(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    original: str
    matched: str
    source_student: str
    similarity: float


class ReportEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    student: str
    score: float
    time: datetime


class SimilarityMatrixEntry(BaseModel):
    pair: str
    avg_similarity: float
    shared_sentences: int


class CollusionGroupResponse(BaseModel):
    total_groups: int
    groups: list[list[str]]


class HeatmapEntry(BaseModel):
    student_a: str
    student_b: str
    similarity: float
    shared_sentences: int
    total_sentences_a: int
    total_sentences_b: int


class SubmissionStatusEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    student_id: UUID
    student_name: str
    submission_id: UUID | None = None
    status: str | None
    submitted_at: datetime | None
    plagiarism_score: float | None


class MySubmissionEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_title: str
    task_code: str
    score: float
    status: str
    submitted_at: datetime


class TaskPublishRequest(BaseModel):
    is_published: bool
