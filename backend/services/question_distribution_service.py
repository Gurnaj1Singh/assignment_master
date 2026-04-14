"""
Question selection and distribution service.

Handles professor selecting questions from the generated pool, and
distributing a random subset to each enrolled student.
"""

import random
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..repositories.classroom_repo import ClassroomRepository
from ..repositories.question_repo import QuestionRepository, StudentQuestionRepo
from ..repositories.submission_repo import TaskRepository


class QuestionDistributionService:
    def __init__(self, db: Session):
        self.db = db
        self.question_repo = QuestionRepository(db)
        self.student_question_repo = StudentQuestionRepo(db)
        self.task_repo = TaskRepository(db)
        self.classroom_repo = ClassroomRepository(db)

    def _validate_task_ownership(self, task_id: UUID, professor_id: UUID):
        """Verify the task exists and the professor owns its classroom."""
        task = self.task_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found.",
            )
        if task.classroom.professor_id != professor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not own this task's classroom.",
            )
        return task

    def select_questions(
        self,
        task_id: UUID,
        question_ids: list[UUID],
        professor_id: UUID,
    ) -> int:
        """
        Mark the given questions as is_selected=True for a task.
        Returns the count of questions selected.
        """
        self._validate_task_ownership(task_id, professor_id)

        # Fetch all questions for this task
        all_questions = self.question_repo.get_by_task(task_id)
        question_map = {q.id: q for q in all_questions}

        selected_count = 0
        for qid in question_ids:
            q = question_map.get(qid)
            if not q:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Question {qid} not found for this task.",
                )
            q.is_selected = True
            selected_count += 1

        self.db.commit()
        return selected_count

    def distribute_questions(
        self,
        task_id: UUID,
        num_per_student: int,
        professor_id: UUID,
    ) -> dict:
        """
        Distribute selected questions randomly to each enrolled student.

        Each student receives num_per_student questions from the selected pool.
        Uses random.sample() for fair distribution.
        """
        task = self._validate_task_ownership(task_id, professor_id)

        # Get selected questions
        selected_questions = self.question_repo.get_selected(task_id)
        if not selected_questions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No questions have been selected. Select questions first.",
            )

        if num_per_student > len(selected_questions):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Requested {num_per_student} questions per student, "
                       f"but only {len(selected_questions)} questions are selected.",
            )

        # Get all enrolled students in the task's classroom
        memberships = self.classroom_repo.get_memberships_for_classroom(
            task.classroom_id
        )
        if not memberships:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No students enrolled in this classroom.",
            )

        # Build assignments
        assignment_dicts = []
        for membership in memberships:
            sampled = random.sample(selected_questions, num_per_student)
            for q in sampled:
                assignment_dicts.append({
                    "student_id": membership.student_id,
                    "question_id": q.id,
                    "task_id": task_id,
                })

        created = self.student_question_repo.assign_questions(assignment_dicts)
        self.db.commit()

        return {
            "total_students": len(memberships),
            "questions_per_student": num_per_student,
            "total_assignments": len(created),
            "assignments": [
                {
                    "student_id": str(a.student_id),
                    "question_id": str(a.question_id),
                }
                for a in created
            ],
        }
