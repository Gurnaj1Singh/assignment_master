"""Aggregates all v1 API routes."""

from fastapi import APIRouter

from . import assignments, auth, classrooms

v1_router = APIRouter()
v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
v1_router.include_router(
    classrooms.router, prefix="/classrooms", tags=["Classrooms"]
)
v1_router.include_router(
    assignments.router, prefix="/assignments", tags=["Assignments"]
)
