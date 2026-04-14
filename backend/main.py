import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from .api.v1.router import v1_router
from .config import settings
from .database import engine, init_db
from .middleware.exception_handler import RequestIDMiddleware, register_exception_handlers
from .middleware.rate_limiter import limiter

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
    version="2.0.0",
    lifespan=lifespan,
)

# --- Rate limiter ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- Middleware (order matters: outermost runs first) ---
app.add_middleware(RequestIDMiddleware)
_cors_origins = ["*"] if settings.CORS_ALLOW_ALL else [settings.FRONTEND_URL]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
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


@app.get("/health")
def health_check():
    """Health check — verifies DB connectivity."""
    db_status = "connected"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"

    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "db": db_status,
        "version": "2.0.0",
    }
