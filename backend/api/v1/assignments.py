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
    HeatmapEntry,
    MySubmissionEntry,
    PlagiarismMatch,
    ReportEntry,
    SimilarityMatrixEntry,
    SubmissionResponse,
    SubmissionStatusEntry,
    TaskPublishRequest,
    VerbatimMatch,
)
from ...schemas.classroom import TaskDetailFullResponse
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
        result = service.process_submission(
            text_content, submission.id, task_id
        )
    except ValueError as exc:
        submission.status = "failed"
        db.commit()
        raise HTTPException(status_code=400, detail=str(exc))

    submission.overall_similarity_score = result.score
    submission.verbatim_flag = result.verbatim_flag
    submission.status = "completed"
    db.commit()

    return SubmissionResponse(
        message="Assignment submitted and analyzed successfully",
        submission_id=submission.id,
        plagiarism_score=f"{result.score}%",
        matches_found=len(result.match_details),
        sentences_processed=result.sentence_count,
        verbatim_flag=result.verbatim_flag,
        verbatim_matches=[
            VerbatimMatch(**vm) for vm in result.verbatim_matches
        ],
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
        SimilarityMatrixEntry(
            pair=f"{m.student_a} & {m.student_b}",
            avg_similarity=round(m.avg_similarity * 100, 2),
            shared_sentences=m.matching_sentences,
        )
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


@router.get("/heatmap/{task_id}", response_model=list[HeatmapEntry])
def get_heatmap(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, "professor", "Unauthorized")
    vector_repo = VectorRepository(db)
    rows = vector_repo.get_heatmap_data(task_id)
    return [
        HeatmapEntry(
            student_a=r.student_a,
            student_b=r.student_b,
            similarity=round(r.similarity, 2),
            shared_sentences=r.shared_sentences,
            total_sentences_a=r.total_sentences_a,
            total_sentences_b=r.total_sentences_b,
        )
        for r in rows
    ]


@router.get("/status/{task_id}", response_model=list[SubmissionStatusEntry])
def get_submission_status(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, "professor", "Unauthorized")

    from ...models.classroom import ClassroomMembership
    from ...models.submission import AssignmentTask as TaskModel, Submission
    from ...models.user import User as UserModel

    task = db.query(TaskModel).filter(
        TaskModel.id == task_id, TaskModel.is_deleted == False  # noqa: E712
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    results = (
        db.query(
            UserModel.id.label("student_id"),
            UserModel.name.label("student_name"),
            Submission.status,
            Submission.created_at.label("submitted_at"),
            Submission.overall_similarity_score.label("plagiarism_score"),
        )
        .select_from(ClassroomMembership)
        .join(UserModel, ClassroomMembership.student_id == UserModel.id)
        .outerjoin(
            Submission,
            (Submission.task_id == task_id)
            & (Submission.student_id == UserModel.id)
            & (Submission.is_deleted == False),  # noqa: E712
        )
        .filter(
            ClassroomMembership.classroom_id == task.classroom_id,
            ClassroomMembership.is_deleted == False,  # noqa: E712
        )
        .all()
    )

    return [
        SubmissionStatusEntry(
            student_id=r.student_id,
            student_name=r.student_name,
            status=r.status or "not_submitted",
            submitted_at=r.submitted_at,
            plagiarism_score=r.plagiarism_score,
        )
        for r in results
    ]


@router.get("/task/{task_id}", response_model=TaskDetailFullResponse)
def get_task_detail(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from ...models.submission import AssignmentTask as TaskModel, Submission
    from sqlalchemy import func

    task = db.query(TaskModel).filter(
        TaskModel.id == task_id, TaskModel.is_deleted == False  # noqa: E712
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    base = {
        "task_id": task.id,
        "title": task.title,
        "description": task.description,
        "assignment_code": task.assignment_code,
        "due_date": task.due_date,
        "is_published": task.is_published,
        "has_pdf": task.assignment_pdf_path is not None,
        "created_at": task.created_at,
    }

    if current_user.role == "professor":
        stats = (
            db.query(
                func.count(Submission.id),
                func.avg(Submission.overall_similarity_score),
            )
            .filter(
                Submission.task_id == task_id,
                Submission.is_deleted == False,  # noqa: E712
            )
            .first()
        )
        base["submission_count"] = stats[0]
        base["average_score"] = round(stats[1], 2) if stats[1] else None
    else:
        if not task.is_published:
            raise HTTPException(status_code=404, detail="Task not found")
        sub = (
            db.query(Submission)
            .filter(
                Submission.task_id == task_id,
                Submission.student_id == current_user.id,
                Submission.is_deleted == False,  # noqa: E712
            )
            .first()
        )
        base["my_status"] = sub.status if sub else "not_submitted"
        base["my_score"] = sub.overall_similarity_score if sub else None

    return TaskDetailFullResponse(**base)


@router.get("/my-submissions", response_model=list[MySubmissionEntry])
def get_my_submissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, "student", "Only students can view their submissions")

    from ...models.submission import AssignmentTask as TaskModel, Submission

    results = (
        db.query(
            TaskModel.title.label("task_title"),
            TaskModel.assignment_code.label("task_code"),
            Submission.overall_similarity_score.label("score"),
            Submission.status,
            Submission.created_at.label("submitted_at"),
        )
        .join(TaskModel, Submission.task_id == TaskModel.id)
        .filter(
            Submission.student_id == current_user.id,
            Submission.is_deleted == False,  # noqa: E712
        )
        .order_by(Submission.created_at.desc())
        .all()
    )

    return [
        MySubmissionEntry(
            task_title=r.task_title,
            task_code=r.task_code,
            score=r.score,
            status=r.status,
            submitted_at=r.submitted_at,
        )
        for r in results
    ]


@router.patch("/task/{task_id}/publish")
def publish_task(
    task_id: UUID,
    request: TaskPublishRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, "professor", "Only professors can publish tasks")

    from ...models.submission import AssignmentTask as TaskModel

    task = db.query(TaskModel).filter(
        TaskModel.id == task_id, TaskModel.is_deleted == False  # noqa: E712
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.classroom.professor_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not own this task")

    task.is_published = request.is_published
    db.commit()

    return {
        "message": f"Task {'published' if request.is_published else 'unpublished'} successfully",
        "task_id": str(task.id),
        "is_published": task.is_published,
    }


@router.get("/collusion-groups/{task_id}", response_model=CollusionGroupResponse)
def get_collusion_groups(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, "professor", "Unauthorized")
    service = GraphService(db)
    return service.find_collusion_groups(task_id)
