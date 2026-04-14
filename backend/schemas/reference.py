"""Pydantic V2 schemas for reference corpus endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ReferenceUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message: str
    reference_id: UUID
    title: str
    sentences_indexed: int
    paragraphs_indexed: int


class ReferenceListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reference_id: UUID
    title: str
    file_path: str
    created_at: datetime
