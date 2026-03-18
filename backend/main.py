import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db, get_db
from .api import auth, assignments, classrooms
from contextlib import asynccontextmanager

# 1. Define the Lifespan Logic
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup Logic ---
    print("Initializing Database...")
    init_db() 
    yield
    # --- Shutdown Logic (if needed) ---
    print("Shutting down server...")

# 2. Pass lifespan to the FastAPI instance
app = FastAPI(title="Assignment Master API", lifespan=lifespan)
# Handle CORS (Essential for React Frontend to talk to Python)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Include Routers (The 'api' folder structure)
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(classrooms.router, prefix="/classrooms", tags=["Classrooms"])
app.include_router(assignments.router, prefix="/assignments", tags=["Assignments"])

@app.get("/")
def read_root():
    return {"status": "Assignment Master Backend is Online"}