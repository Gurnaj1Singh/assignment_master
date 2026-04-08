"""
Classrooms API — /classrooms/...
==================================
Handles everything related to classrooms and assignment tasks:

  POST /classrooms/create              → professor creates a classroom
  POST /classrooms/join/{class_code}   → student enrolls in a classroom
  GET  /classrooms/my                  → list all classrooms for current user
  GET  /classrooms/{classroom_id}/members  → professor views enrolled students
  POST /classrooms/{classroom_id}/tasks    → professor creates an assignment task

All endpoints require a valid JWT (via get_current_user dependency).
Role-based access is enforced at the start of each handler.
"""

import string
import random
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ..database import get_db
from ..models import AssignmentTask, Classroom, ClassroomMembership, User
from .auth import get_current_user


router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------

class ClassroomCreateRequest(BaseModel):
    class_name: str = Field(..., min_length=2, max_length=200,
                            description="Human-readable name, e.g. 'Robotics & AI'")

class TaskCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=300,
                       description="Assignment title, e.g. 'NLP Research Paper'")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generate_code(length: int = 6) -> str:
    """Returns a random uppercase alphanumeric code of the given length."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(random.choices(alphabet, k=length))


def _require_role(user: User, role: str, detail: str) -> None:
    """Raises HTTP 403 if the current user does not have the expected role."""
    if user.role != role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


# ---------------------------------------------------------------------------
# POST /classrooms/create
# ---------------------------------------------------------------------------

@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_classroom(
    request: ClassroomCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Professor creates a new classroom.

    Returns the generated class_code — professors share this code with
    students so they can enrol via POST /classrooms/join/{class_code}.
    """
    _require_role(current_user, "professor", "Only professors can create classrooms.")

    # Keep generating until we get a code that isn't already taken.
    # Collisions are extremely rare with a 6-char code space (~2.1 billion combos)
    # but we guard against them defensively.
    for _ in range(5):
        code = _generate_code()
        if not db.query(Classroom).filter(Classroom.class_code == code).first():
            break
    else:
        # All 5 attempts collided — pathologically unlikely, but safe to handle
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate a unique classroom code. Please try again.",
        )

    new_classroom = Classroom(
        class_name=request.class_name,
        class_code=code,
        professor_id=current_user.id,
    )
    db.add(new_classroom)
    db.commit()
    db.refresh(new_classroom)

    return {
        "message": "Classroom created successfully.",
        "class_id": str(new_classroom.id),
        "class_name": new_classroom.class_name,
        "class_code": new_classroom.class_code,
    }


# ---------------------------------------------------------------------------
# POST /classrooms/join/{class_code}
# ---------------------------------------------------------------------------

@router.post("/join/{class_code}", status_code=status.HTTP_200_OK)
async def join_classroom(
    class_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Student enrols in a classroom using its 6-character code.

    Previously this endpoint only returned a success message without saving
    anything to the database. Now it creates a `ClassroomMembership` record,
    which permanently links the student to the classroom.

    Errors:
      403 — caller is not a student
      404 — class_code does not match any classroom
      409 — student is already enrolled in this classroom
    """
    _require_role(current_user, "student", "Only students can join classrooms.")

    # Look up the classroom by code (case-insensitive)
    classroom = (
        db.query(Classroom)
        .filter(Classroom.class_code == class_code.upper())
        .first()
    )
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No classroom found with code '{class_code.upper()}'.",
        )

    # Check if the student is already enrolled (prevents duplicate memberships)
    already_enrolled = (
        db.query(ClassroomMembership)
        .filter(
            ClassroomMembership.classroom_id == classroom.id,
            ClassroomMembership.student_id == current_user.id,
        )
        .first()
    )
    if already_enrolled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"You are already enrolled in '{classroom.class_name}'.",
        )

    # Persist the membership
    membership = ClassroomMembership(
        classroom_id=classroom.id,
        student_id=current_user.id,
    )
    db.add(membership)

    try:
        db.commit()
    except IntegrityError:
        # Race condition: two simultaneous requests for the same student+classroom.
        # The DB UniqueConstraint catches it; we surface a clean 409 instead of a 500.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"You are already enrolled in '{classroom.class_name}'.",
        )

    return {
        "message": f"Successfully enrolled in '{classroom.class_name}'.",
        "class_id": str(classroom.id),
        "class_name": classroom.class_name,
    }


# ---------------------------------------------------------------------------
# GET /classrooms/my
# ---------------------------------------------------------------------------

@router.get("/my", status_code=status.HTTP_200_OK)
async def get_my_classrooms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns all classrooms relevant to the current user:
      - Professors: classrooms they own
      - Students: classrooms they are enrolled in
    """
    if current_user.role == "professor":
        classrooms = (
            db.query(Classroom)
            .filter(Classroom.professor_id == current_user.id)
            .all()
        )
        return [
            {
                "class_id": str(c.id),
                "class_name": c.class_name,
                "class_code": c.class_code,
                "created_at": c.created_at,
                "student_count": len(c.memberships),
            }
            for c in classrooms
        ]

    else:  # student
        memberships = (
            db.query(ClassroomMembership)
            .filter(ClassroomMembership.student_id == current_user.id)
            .all()
        )
        return [
            {
                "class_id": str(m.classroom.id),
                "class_name": m.classroom.class_name,
                "class_code": m.classroom.class_code,
                "joined_at": m.joined_at,
            }
            for m in memberships
        ]


# ---------------------------------------------------------------------------
# GET /classrooms/{classroom_id}/members
# ---------------------------------------------------------------------------

@router.get("/{classroom_id}/members", status_code=status.HTTP_200_OK)
async def get_classroom_members(
    classroom_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns the list of enrolled students for a classroom.
    Only the professor who owns the classroom can call this.
    """
    _require_role(current_user, "professor", "Only professors can view classroom members.")

    classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found.")

    if classroom.professor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this classroom.",
        )

    members = (
        db.query(ClassroomMembership)
        .filter(ClassroomMembership.classroom_id == classroom_id)
        .all()
    )

    return {
        "class_name": classroom.class_name,
        "class_code": classroom.class_code,
        "total_students": len(members),
        "students": [
            {
                "student_id": str(m.student_id),
                "name": m.student.name,
                "email": m.student.email,
                "joined_at": m.joined_at,
            }
            for m in members
        ],
    }


# ---------------------------------------------------------------------------
# POST /classrooms/{classroom_id}/tasks
# ---------------------------------------------------------------------------

@router.post("/{classroom_id}/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(
    classroom_id: UUID,
    request: TaskCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Professor creates an assignment task inside a classroom.

    Returns a unique assignment_code that students include when submitting
    their PDFs via POST /assignments/submit/{task_id}.
    """
    _require_role(current_user, "professor", "Only professors can create tasks.")

    # Verify the classroom exists and belongs to this professor
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found.")
    if classroom.professor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this classroom.",
        )

    task_code = _generate_code()
    new_task = AssignmentTask(
        classroom_id=classroom_id,
        title=request.title,
        assignment_code=task_code,
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return {
        "message": "Assignment task created successfully.",
        "task_id": str(new_task.id),
        "task_code": new_task.assignment_code,
        "title": new_task.title,
    }
