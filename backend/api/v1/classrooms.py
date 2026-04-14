"""Classroom management routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.user import User
from ...schemas.classroom import (
    ClassroomCreateRequest,
    ClassroomMemberResponse,
    TaskCreateRequest,
    TaskListEntry,
)
from ...services.classroom_service import ClassroomService
from ..deps import get_current_user, require_role

router = APIRouter()


@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_classroom(
    request: ClassroomCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, "professor", "Only professors can create classrooms.")
    service = ClassroomService(db)
    classroom = service.create_classroom(request.class_name, current_user.id)
    return {
        "message": "Classroom created successfully.",
        "class_id": str(classroom.id),
        "class_name": classroom.class_name,
        "class_code": classroom.class_code,
    }


@router.post("/join/{class_code}", status_code=status.HTTP_200_OK)
def join_classroom(
    class_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, "student", "Only students can join classrooms.")
    service = ClassroomService(db)
    classroom = service.join_classroom(class_code, current_user.id)
    return {
        "message": f"Successfully enrolled in '{classroom.class_name}'.",
        "class_id": str(classroom.id),
        "class_name": classroom.class_name,
    }


@router.get("/my", status_code=status.HTTP_200_OK)
def get_my_classrooms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ClassroomService(db)
    if current_user.role == "professor":
        return service.get_classrooms_for_professor(current_user.id)
    return service.get_classrooms_for_student(current_user.id)


@router.get("/{classroom_id}/members", response_model=ClassroomMemberResponse)
def get_classroom_members(
    classroom_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, "professor", "Only professors can view classroom members.")
    service = ClassroomService(db)
    return service.get_classroom_members(classroom_id, current_user.id)


@router.get("/{classroom_id}/tasks", response_model=list[TaskListEntry])
def list_tasks(
    classroom_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from ...models.submission import AssignmentTask, Submission
    from sqlalchemy import func

    service = ClassroomService(db)
    classroom = service.classroom_repo.get_by_id(classroom_id)
    if not classroom:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Classroom not found")

    query = (
        db.query(
            AssignmentTask,
            func.count(Submission.id).label("submission_count"),
        )
        .outerjoin(
            Submission,
            (Submission.task_id == AssignmentTask.id)
            & (Submission.is_deleted == False),  # noqa: E712
        )
        .filter(
            AssignmentTask.classroom_id == classroom_id,
            AssignmentTask.is_deleted == False,  # noqa: E712
        )
        .group_by(AssignmentTask.id)
        .order_by(AssignmentTask.created_at.desc())
    )

    # Students only see published tasks
    if current_user.role == "student":
        query = query.filter(AssignmentTask.is_published == True)  # noqa: E712

    results = query.all()

    return [
        TaskListEntry(
            task_id=task.id,
            title=task.title,
            description=task.description,
            assignment_code=task.assignment_code,
            due_date=task.due_date,
            is_published=task.is_published,
            has_pdf=task.assignment_pdf_path is not None,
            submission_count=count,
            created_at=task.created_at,
        )
        for task, count in results
    ]


@router.post("/{classroom_id}/tasks", status_code=status.HTTP_201_CREATED)
def create_task(
    classroom_id: UUID,
    request: TaskCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, "professor", "Only professors can create tasks.")
    service = ClassroomService(db)
    task = service.create_task(
        classroom_id,
        request.title,
        current_user.id,
        description=request.description,
        due_date=request.due_date,
    )
    return {
        "message": "Assignment task created successfully.",
        "task_id": str(task.id),
        "task_code": task.assignment_code,
        "title": task.title,
        "due_date": task.due_date,
    }
