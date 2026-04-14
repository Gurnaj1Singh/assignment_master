"""Business logic for reference corpus upload and management."""

import os
import uuid
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ..models.reference import ReferenceDocument
from ..repositories.reference_repo import (
    ReferenceDocumentRepository,
    ReferenceVectorRepository,
)
from ..repositories.submission_repo import TaskRepository
from ..services.nlp_service import NLPService
from ..services.pdf_service import extract_text_from_pdf

BASE_DIR = Path(__file__).resolve().parent.parent.parent
REFERENCE_DIR = os.path.join(BASE_DIR, "uploads", "references")
os.makedirs(REFERENCE_DIR, exist_ok=True)


class ReferenceService:
    def __init__(self, db: Session):
        self.db = db
        self.doc_repo = ReferenceDocumentRepository(db)
        self.vec_repo = ReferenceVectorRepository(db)
        self.task_repo = TaskRepository(db)

    def upload_reference(
        self,
        task_id: UUID,
        professor_id: UUID,
        file: UploadFile,
        nlp: NLPService,
    ) -> dict:
        """
        Full pipeline: validate ownership → save PDF → extract text →
        chunk → embed sentences + paragraphs → persist → commit.

        Returns a dict suitable for ReferenceUploadResponse.
        """
        # --- Ownership validation ---
        task = self.task_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found.",
            )
        if task.classroom.professor_id != professor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not own this task.",
            )

        # --- Validate and save PDF ---
        content = file.file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )

        file_name = f"{uuid.uuid4()}.pdf"
        abs_path = os.path.join(REFERENCE_DIR, file_name)

        with open(abs_path, "wb") as buffer:
            buffer.write(content)

        try:
            text_content = extract_text_from_pdf(abs_path)
        except ValueError as exc:
            os.remove(abs_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            )

        # Relative path — robust across deployments
        relative_path = os.path.join("uploads", "references", file_name)

        # --- Create ReferenceDocument record ---
        title = file.filename or file_name
        doc = self.doc_repo.create(
            task_id=task_id,
            title=title,
            file_path=relative_path,
            uploaded_by=professor_id,
        )

        # --- Chunk and embed ---
        paragraphs, sentences = nlp.get_chunks(text_content)

        if not sentences:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No readable sentences found in the reference PDF.",
            )

        sentence_embeddings = nlp.generate_embeddings(sentences)
        self.vec_repo.bulk_create(
            reference_id=doc.id,
            chunks=sentences,
            embeddings=sentence_embeddings,
            vec_type="sentence",
        )

        paragraph_embeddings = nlp.generate_embeddings(paragraphs) if paragraphs else []
        if paragraphs:
            self.vec_repo.bulk_create(
                reference_id=doc.id,
                chunks=paragraphs,
                embeddings=paragraph_embeddings,
                vec_type="paragraph",
            )

        self.db.commit()
        self.db.refresh(doc)

        return {
            "message": "Reference document uploaded and indexed successfully.",
            "reference_id": doc.id,
            "title": doc.title,
            "sentences_indexed": len(sentences),
            "paragraphs_indexed": len(paragraphs),
        }

    def list_references(self, task_id: UUID, professor_id: UUID) -> list[ReferenceDocument]:
        """Return all active reference documents for a task (ownership-checked)."""
        task = self.task_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found.",
            )
        if task.classroom.professor_id != professor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not own this task.",
            )
        return self.doc_repo.get_by_task(task_id)

    def delete_reference(
        self, reference_id: UUID, professor_id: UUID
    ) -> ReferenceDocument:
        """Soft-delete a reference document (ownership-checked)."""
        doc = self.doc_repo.get_by_id(reference_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reference document not found.",
            )
        if doc.task.classroom.professor_id != professor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not own this reference document.",
            )
        self.doc_repo.soft_delete(reference_id, deleted_by=professor_id)
        self.db.commit()
        return doc
