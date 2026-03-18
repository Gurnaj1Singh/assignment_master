from sqlalchemy import Column, String, Float, Integer, ForeignKey, Text, DateTime, Enum, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    role = Column(String) # 'professor' or 'student'
    submissions = relationship("Submission", back_populates="student")

class Classroom(Base):
    __tablename__ = "classrooms"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    professor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    class_name = Column(String, nullable=False)
    class_code = Column(String, unique=True, nullable=False)

class AssignmentTask(Base):
    __tablename__ = "assignment_tasks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    classroom_id = Column(UUID(as_uuid=True), ForeignKey("classrooms.id"))
    title = Column(String, nullable=False)
    assignment_code = Column(String, unique=True, nullable=False)

    # Add this line so we can easily find all submissions for a task
    submissions = relationship("Submission", backref="task")

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("assignment_tasks.id"))
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    overall_similarity_score = Column(Float, default=0.0)
    submitted_at = Column(DateTime, server_default=func.now())
    file_path = Column(Text)
    student = relationship("User", back_populates="submissions")
    vectors = relationship("TextVector", back_populates="submission")

class TextVector(Base):
    __tablename__ = "text_vectors"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id"))
    content_chunk = Column(Text, nullable=False)
    # This is where the magic happens: Vector(768)
    embedding = Column(Vector(768)) 
    type = Column(String) # 'sentence' or 'paragraph'
    seq_order = Column(Integer)

    submission = relationship("Submission", back_populates="vectors")

