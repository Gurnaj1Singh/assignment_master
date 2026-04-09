import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.router import v1_router
from .database import init_db
from .middleware.exception_handler import RequestIDMiddleware, register_exception_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    init_db()
    yield
    logger.info("Shutting down server...")


app = FastAPI(
    title="Assignment Master API",
    version="1.0.0",
    lifespan=lifespan,
)

# --- Middleware (order matters: outermost runs first) ---
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict to frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global exception handlers ---
register_exception_handlers(app)

# --- Versioned API routes ---
app.include_router(v1_router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"status": "Assignment Master Backend is Online"}