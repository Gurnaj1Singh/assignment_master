"""Classroom and task business logic."""

import random
import string
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models.classroom import Classroom
from ..models.submission import AssignmentTask
from ..repositories.classroom_repo import ClassroomRepository
from ..repositories.submission_repo import TaskRepository


def _generate_code(length: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(random.choices(alphabet, k=length))


class ClassroomService:
    def __init__(self, db: Session):
        self.db = db
        self.classroom_repo = ClassroomRepository(db)
        self.task_repo = TaskRepository(db)

    def create_classroom(self, class_name: str, professor_id: UUID) -> Classroom:
        for _ in range(5):
            code = _generate_code()
            if not self.classroom_repo.get_by_code(code):
                break
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not generate a unique classroom code. Try again.",
            )

        classroom = self.classroom_repo.create(
            class_name=class_name,
            class_code=code,
            professor_id=professor_id,
        )
        self.db.commit()
        self.db.refresh(classroom)
        return classroom

    def join_classroom(self, class_code: str, student_id: UUID) -> Classroom:
        classroom = self.classroom_repo.get_by_code(class_code)
        if not classroom:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No classroom found with code '{class_code.upper()}'.",
            )

        if self.classroom_repo.get_membership(classroom.id, student_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"You are already enrolled in '{classroom.class_name}'.",
            )

        self.classroom_repo.create_membership(classroom.id, student_id)

        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"You are already enrolled in '{classroom.class_name}'.",
            )

        return classroom

    def get_classrooms_for_professor(self, professor_id: UUID) -> list[dict]:
        classrooms = self.classroom_repo.get_by_professor(professor_id)
        return [
            {
                "class_id": c.id,
                "class_name": c.class_name,
                "class_code": c.class_code,
                "created_at": c.created_at,
                "student_count": len(c.memberships),
            }
            for c in classrooms
        ]

    def get_classrooms_for_student(self, student_id: UUID) -> list[dict]:
        memberships = self.classroom_repo.get_memberships_for_student(student_id)
        return [
            {
                "class_id": m.classroom.id,
                "class_name": m.classroom.class_name,
                "class_code": m.classroom.class_code,
                "joined_at": m.joined_at,
            }
            for m in memberships
        ]

    def get_classroom_members(
        self, classroom_id: UUID, professor_id: UUID
    ) -> dict:
        classroom = self.classroom_repo.get_by_id(classroom_id)
        if not classroom:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Classroom not found.",
            )
        if classroom.professor_id != professor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not own this classroom.",
            )

        members = self.classroom_repo.get_memberships_for_classroom(classroom_id)
        return {
            "class_name": classroom.class_name,
            "class_code": classroom.class_code,
            "total_students": len(members),
            "students": [
                {
                    "student_id": m.student_id,
                    "name": m.student.name,
                    "email": m.student.email,
                    "joined_at": m.joined_at,
                }
                for m in members
            ],
        }

    def create_task(
        self,
        classroom_id: UUID,
        title: str,
        professor_id: UUID,
        description: str | None = None,
        due_date=None,
    ) -> AssignmentTask:
        classroom = self.classroom_repo.get_by_id(classroom_id)
        if not classroom:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Classroom not found.",
            )
        if classroom.professor_id != professor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not own this classroom.",
            )

        task = self.task_repo.create(
            classroom_id=classroom_id,
            title=title,
            description=description,
            due_date=due_date,
            assignment_code=_generate_code(),
        )
        self.db.commit()
        self.db.refresh(task)
        return task

    def attach_task_pdf(
        self, task_id: UUID, professor_id: UUID, pdf_path: str
    ) -> AssignmentTask:
        """
        Attach an uploaded question-paper PDF to an existing task.
        Only the professor who owns the task's classroom may do this.
        """
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

        task.assignment_pdf_path = pdf_path
        self.db.commit()
        self.db.refresh(task)
        return task
