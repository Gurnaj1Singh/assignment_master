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


@router.post("/{classroom_id}/tasks", status_code=status.HTTP_201_CREATED)
def create_task(
    classroom_id: UUID,
    request: TaskCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, "professor", "Only professors can create tasks.")
    service = ClassroomService(db)
    task = service.create_task(classroom_id, request.title, current_user.id)
    return {
        "message": "Assignment task created successfully.",
        "task_id": str(task.id),
        "task_code": task.assignment_code,
        "title": task.title,
    }
