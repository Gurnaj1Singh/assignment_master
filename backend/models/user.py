import uuid

from sqlalchemy import Column, Enum, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, SoftDeleteMixin, TimestampMixin


class User(TimestampMixin, SoftDeleteMixin, Base):
    """
    role='professor' -> can create classrooms, create tasks, view reports.
    role='student'   -> can join classrooms, submit assignments.
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    role = Column(Enum("student", "professor", name="user_role"),nullable=False)

    memberships = relationship(
        "ClassroomMembership",
        back_populates="student",
        cascade="all, delete-orphan",
    )
    submissions = relationship(
        "Submission",
        back_populates="student",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"
