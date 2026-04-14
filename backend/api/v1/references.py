"""
Reference corpus API routes.

All endpoints are synchronous (def, not async def) — file I/O and SBERT
inference run in FastAPI's threadpool and do not block the event loop.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.user import User
from ...schemas.reference import ReferenceListResponse, ReferenceUploadResponse
from ...services.nlp_service import NLPService, get_nlp_service
from ...services.reference_service import ReferenceService
from ..deps import get_current_user, require_role

router = APIRouter()


@router.post("/upload/{task_id}", response_model=ReferenceUploadResponse, status_code=201)
def upload_reference(
    task_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    nlp: NLPService = Depends(get_nlp_service),
):
    """
    Professor uploads a reference PDF for an assignment task.

    The PDF is validated, saved to uploads/references/, and chunked into
    sentences and paragraphs whose SBERT embeddings are stored for later
    source-exclusion matching and RAG retrieval.
    """
    require_role(current_user, "professor", "Only professors can upload reference documents.")

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    service = ReferenceService(db)
    result = service.upload_reference(
        task_id=task_id,
        professor_id=current_user.id,
        file=file,
        nlp=nlp,
    )
    return ReferenceUploadResponse(**result)


@router.get("/list/{task_id}", response_model=list[ReferenceListResponse])
def list_references(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all reference documents uploaded for a task."""
    require_role(current_user, "professor", "Only professors can view reference documents.")

    service = ReferenceService(db)
    docs = service.list_references(task_id=task_id, professor_id=current_user.id)
    return [
        ReferenceListResponse(
            reference_id=doc.id,
            title=doc.title,
            file_path=doc.file_path,
            created_at=doc.created_at,
        )
        for doc in docs
    ]


@router.delete("/{reference_id}", status_code=200)
def delete_reference(
    reference_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete a reference document."""
    require_role(current_user, "professor", "Only professors can delete reference documents.")

    service = ReferenceService(db)
    doc = service.delete_reference(
        reference_id=reference_id,
        professor_id=current_user.id,
    )
    return {
        "message": "Reference document deleted successfully.",
        "reference_id": str(doc.id),
        "title": doc.title,
    }
