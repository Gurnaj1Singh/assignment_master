from uuid import UUID

from sqlalchemy.orm import Session

from ..models.classroom import Classroom, ClassroomMembership
from .base import BaseRepository


class ClassroomRepository(BaseRepository[Classroom]):
    def __init__(self, db: Session):
        super().__init__(Classroom, db)

    def get_by_code(self, code: str) -> Classroom | None:
        return (
            self._base_query()
            .filter(Classroom.class_code == code.upper())
            .first()
        )

    def get_by_professor(self, professor_id: UUID) -> list[Classroom]:
        return (
            self._base_query()
            .filter(Classroom.professor_id == professor_id)
            .all()
        )

    def get_membership(
        self, classroom_id: UUID, student_id: UUID
    ) -> ClassroomMembership | None:
        return (
            self.db.query(ClassroomMembership)
            .filter(
                ClassroomMembership.classroom_id == classroom_id,
                ClassroomMembership.student_id == student_id,
                ClassroomMembership.is_deleted == False,  # noqa: E712
            )
            .first()
        )

    def create_membership(
        self, classroom_id: UUID, student_id: UUID
    ) -> ClassroomMembership:
        m = ClassroomMembership(
            classroom_id=classroom_id, student_id=student_id
        )
        self.db.add(m)
        self.db.flush()
        return m

    def get_memberships_for_student(
        self, student_id: UUID
    ) -> list[ClassroomMembership]:
        return (
            self.db.query(ClassroomMembership)
            .filter(
                ClassroomMembership.student_id == student_id,
                ClassroomMembership.is_deleted == False,  # noqa: E712
            )
            .all()
        )

    def get_memberships_for_classroom(
        self, classroom_id: UUID
    ) -> list[ClassroomMembership]:
        return (
            self.db.query(ClassroomMembership)
            .filter(
                ClassroomMembership.classroom_id == classroom_id,
                ClassroomMembership.is_deleted == False,  # noqa: E712
            )
            .all()
        )
