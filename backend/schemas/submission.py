"""Submission and plagiarism response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message: str
    submission_id: UUID
    plagiarism_score: str
    matches_found: int
    sentences_processed: int


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
    shared_sentences: int


class CollusionGroupResponse(BaseModel):
    total_groups: int
    groups: list[list[str]]
