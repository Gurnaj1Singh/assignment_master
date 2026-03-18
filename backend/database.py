from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base


SQLALCHEMY_DATABASE_URL = "postgresql://postgres:gsm1234@localhost:5432/assignment_master"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    # Ensure pgvector is enabled before creating tables
    with engine.connect() as conn:
        from sqlalchemy import text
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()
    
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized successfully.")

def get_db():
    """
    Dependency to get a DB session for FastAPI endpoints.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()