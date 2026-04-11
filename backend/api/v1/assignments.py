"""
Assignment submission and plagiarism analysis routes.

NOTE: submit_assignment uses `def` (not `async def`) so FastAPI runs it
in a threadpool — SBERT inference and PDF parsing will not block the
event loop.
"""

import os
import uuid as uuid_mod
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.user import User
from ...repositories.submission_repo import SubmissionRepository
from ...repositories.vector_repo import VectorRepository
from ...schemas.submission import (
    CollusionGroupResponse,
    PlagiarismMatch,
    ReportEntry,
    SimilarityMatrixEntry,
    SubmissionResponse,
)
from ...services.classroom_service import ClassroomService
from ...services.graph_service import GraphService
from ...services.nlp_service import NLPService, get_nlp_service
from ...services.pdf_service import extract_text_from_pdf
from ...services.plagiarism_service import PlagiarismService
from ..deps import get_current_user, require_role

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Student submission PDFs
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads", "assignments")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Professor question-paper PDFs (kept separate from student submissions)
TASK_PDF_DIR = os.path.join(BASE_DIR, "uploads", "tasks")
os.makedirs(TASK_PDF_DIR, exist_ok=True)


@router.post("/submit/{task_id}", response_model=SubmissionResponse)
def submit_assignment(
    task_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    nlp: NLPService = Depends(get_nlp_service),
):
    """
    Synchronous handler (def, not async def) — runs in threadpool so
    SBERT inference does not block the event loop.
    """
    require_role(current_user, "student", "Only students can submit assignments")

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    file_name = f"{uuid_mod.uuid4()}.pdf"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    content = file.file.read()
    with open(file_path, "wb") as buffer:
        buffer.write(content)

    try:
        text_content = extract_text_from_pdf(file_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    submission_repo = SubmissionRepository(db)
    submission = submission_repo.create(
        task_id=task_id,
        student_id=current_user.id,
        file_path=file_path,
        status="processing",
    )
    db.flush()

    service = PlagiarismService(db, nlp)
    try:
        score, details, sentence_count = service.process_submission(
            text_content, submission.id, task_id
        )
    except ValueError as exc:
        submission.status = "failed"
        db.commit()
        raise HTTPException(status_code=400, detail=str(exc))

    submission.overall_similarity_score = score
    submission.status = "completed"
    db.commit()

    return SubmissionResponse(
        message="Assignment submitted and analyzed successfully",
        submission_id=submission.id,
        plagiarism_score=f"{score}%",
        matches_found=len(details),
        sentences_processed=sentence_count,
    )


@router.post("/task-pdf/{task_id}", status_code=200)
def upload_task_pdf(
    task_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Professor uploads a question-paper PDF for an existing task.

    Stored in uploads/tasks/ (separate from student submissions in uploads/assignments/).
    The file_path stored in the DB is RELATIVE to TASK_PDF_DIR so it survives
    server migrations.

    This endpoint is intentionally synchronous (def, not async def) — file I/O
    runs in a threadpool and does not block the event loop.
    """
    require_role(current_user, "professor", "Only professors can upload task PDFs.")

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    # Validate the PDF is readable before saving — fail fast, not after storage
    content = file.file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    file_name = f"{uuid_mod.uuid4()}.pdf"
    abs_path = os.path.join(TASK_PDF_DIR, file_name)

    with open(abs_path, "wb") as buffer:
        buffer.write(content)

    # Verify the saved file is a valid PDF (not a renamed .exe etc.)
    try:
        extract_text_from_pdf(abs_path)
    except ValueError as exc:
        os.remove(abs_path)  # clean up the invalid file
        raise HTTPException(status_code=400, detail=str(exc))

    # Store relative path — robust across deployments
    relative_path = os.path.join("uploads", "tasks", file_name)

    service = ClassroomService(db)
    task = service.attach_task_pdf(task_id, current_user.id, relative_path)

    return {
        "message": "Task PDF uploaded successfully.",
        "task_id": str(task.id),
        "title": task.title,
        "pdf_path": task.assignment_pdf_path,
    }


@router.get("/report/{task_id}", response_model=list[ReportEntry])
def get_assignment_report(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, "professor", "Unauthorized")

    from ...models.submission import Submission
    from ...models.user import User as UserModel

    results = (
        db.query(UserModel.name, Submission.overall_similarity_score, Submission.created_at)
        .join(Submission, UserModel.id == Submission.student_id)
        .filter(Submission.task_id == task_id, Submission.is_deleted == False)  # noqa: E712
        .order_by(Submission.overall_similarity_score.desc())
        .all()
    )

    return [
        ReportEntry(student=r[0], score=r[1], time=r[2]) for r in results
    ]


@router.get("/matrix/{task_id}", response_model=list[SimilarityMatrixEntry])
def get_similarity_matrix(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, "professor", "Unauthorized")
    vector_repo = VectorRepository(db)
    matrix = vector_repo.get_similarity_matrix(task_id)
    return [
        SimilarityMatrixEntry(pair=f"{m[0]} & {m[1]}", shared_sentences=m[2])
        for m in matrix
    ]


@router.get("/submission-detail/{submission_id}", response_model=list[PlagiarismMatch])
def get_submission_detail(
    submission_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, "professor", "Unauthorized")
    vector_repo = VectorRepository(db)
    matches = vector_repo.get_submission_matches(submission_id)
    return [
        PlagiarismMatch(
            original=m.student_text,
            matched=m.matched_text,
            source_student=m.copied_from,
            similarity=round(m.similarity * 100, 2),
        )
        for m in matches
    ]


@router.get("/collusion-groups/{task_id}", response_model=CollusionGroupResponse)
def get_collusion_groups(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, "professor", "Unauthorized")
    service = GraphService(db)
    return service.find_collusion_groups(task_id)
