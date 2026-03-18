import string
import random
from uuid import UUID 
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Classroom, User, AssignmentTask
from .auth import get_current_user
from pydantic import BaseModel

router = APIRouter()

class ClassroomCreate(BaseModel):
    class_name: str

def generate_class_code(length=6):
    """Generates a random alphanumeric code for the classroom."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

@router.post("/create")
async def create_classroom(
    request: ClassroomCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # 1. Authorization Check: Only professors can create classes
    if current_user.role != "professor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only professors can create classrooms."
        )

    # 2. Generate a unique code
    code = generate_class_code()
    
    # 3. Save to Database
    new_class = Classroom(
        class_name=request.class_name,
        class_code=code,
        professor_id=current_user.id
    )
    
    db.add(new_class)
    db.commit()
    db.refresh(new_class)
    
    return {
        "message": "Classroom created successfully",
        "class_code": code,
        "class_id": new_class.id
    }

@router.post("/join/{class_code}")
async def join_classroom(
    class_code: str, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # 1. Validation: Only students join classes (typically)
    if current_user.role != "student":
        raise HTTPException(
            status_code=403, 
            detail="Professors cannot join classes as students."
        )

    # 2. Find the classroom by code
    classroom = db.query(Classroom).filter(Classroom.class_code == class_code).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Invalid classroom code.")

    # 3. Check if student is already in this class (Prevent duplicates)
    # Note: This assumes you have a Many-to-Many table or a link. 
    # For a simple project, we'll return a success message 
    # and link them in the assignments phase.

    return {
        "message": f"Successfully joined {classroom.class_name}",
        "class_id": classroom.id
    }

class TaskCreate(BaseModel):
    title: str

@router.post("/{classroom_id}/tasks")
async def create_task(
    classroom_id: UUID, 
    request: TaskCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "professor":
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    task_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    new_task = AssignmentTask(
        classroom_id=classroom_id,
        title=request.title,
        assignment_code=task_code
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return {"task_id": new_task.id, "task_code": task_code}