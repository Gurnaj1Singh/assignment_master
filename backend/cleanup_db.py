from sqlalchemy import text
from database import SessionLocal

def reset_project_data():
    db = SessionLocal()
    print("🧹 Cleaning up all project data...")
    try:
        # We delete in order of dependencies (Text Vectors first, then Users)
        db.execute(text("TRUNCATE text_vectors, submissions, assignment_tasks, classrooms, users RESTART IDENTITY CASCADE;"))
        db.commit()
        print("✨ Database is now fresh and ready for the demo!")
    except Exception as e:
        db.rollback()
        print(f"❌ Cleanup failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_project_data()