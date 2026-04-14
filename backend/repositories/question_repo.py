"""Repositories for LLM-generated questions and student assignments."""

from uuid import UUID

from sqlalchemy.orm import Session

from ..models.question import GeneratedQuestion, StudentQuestionAssignment
from .base import BaseRepository


class QuestionRepository(BaseRepository[GeneratedQuestion]):
    def __init__(self, db: Session):
        super().__init__(GeneratedQuestion, db)

    def get_by_task(self, task_id: UUID) -> list[GeneratedQuestion]:
        """Return all non-deleted generated questions for a task."""
        return (
            self._base_query()
            .filter(GeneratedQuestion.task_id == task_id)
            .order_by(GeneratedQuestion.created_at.asc())
            .all()
        )

    def get_selected(self, task_id: UUID) -> list[GeneratedQuestion]:
        """Return only professor-selected questions for a task."""
        return (
            self._base_query()
            .filter(
                GeneratedQuestion.task_id == task_id,
                GeneratedQuestion.is_selected == True,  # noqa: E712
            )
            .order_by(GeneratedQuestion.created_at.asc())
            .all()
        )

    def bulk_create(self, questions: list[dict]) -> list[GeneratedQuestion]:
        """Insert multiple generated questions at once. Flushes, does not commit."""
        objs = []
        for q in questions:
            obj = GeneratedQuestion(**q)
            self.db.add(obj)
            objs.append(obj)
        self.db.flush()
        return objs


class StudentQuestionRepo:
    def __init__(self, db: Session):
        self.db = db

    def assign_questions(
        self,
        assignments: list[dict],
    ) -> list[StudentQuestionAssignment]:
        """Bulk-create student-question assignments. Flushes, does not commit."""
        objs = []
        for a in assignments:
            obj = StudentQuestionAssignment(**a)
            self.db.add(obj)
            objs.append(obj)
        self.db.flush()
        return objs

    def get_for_student(
        self, student_id: UUID, task_id: UUID
    ) -> list[StudentQuestionAssignment]:
        """Return all question assignments for a student on a given task."""
        return (
            self.db.query(StudentQuestionAssignment)
            .filter(
                StudentQuestionAssignment.student_id == student_id,
                StudentQuestionAssignment.task_id == task_id,
            )
            .all()
        )
