from uuid import UUID

from sqlalchemy.orm import Session

from ..models.submission import AssignmentTask, Submission
from .base import BaseRepository


class SubmissionRepository(BaseRepository[Submission]):
    def __init__(self, db: Session):
        super().__init__(Submission, db)

    def get_by_task(self, task_id: UUID) -> list[Submission]:
        return (
            self._base_query()
            .filter(Submission.task_id == task_id)
            .all()
        )


class TaskRepository(BaseRepository[AssignmentTask]):
    def __init__(self, db: Session):
        super().__init__(AssignmentTask, db)

    def get_by_classroom(self, classroom_id: UUID) -> list[AssignmentTask]:
        return (
            self._base_query()
            .filter(AssignmentTask.classroom_id == classroom_id)
            .all()
        )
