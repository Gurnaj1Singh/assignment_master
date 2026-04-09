"""
Architecture validation tests.

These tests verify that the layered architecture is properly structured:
- Models load with mixins
- Schemas validate correctly
- Repositories inherit properly
- Services instantiate
- Routes register on the app
- Singleton NLP pattern holds
"""

import importlib
import sys
import os

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


# ─── Model Layer ────────────────────────────────────────────────────

class TestModels:
    def test_base_imports(self):
        from backend.models.base import Base, TimestampMixin, SoftDeleteMixin
        assert Base is not None
        assert hasattr(TimestampMixin, "created_at")
        assert hasattr(TimestampMixin, "updated_at")
        assert hasattr(SoftDeleteMixin, "is_deleted")

    def test_user_has_mixins(self):
        from backend.models.user import User
        assert hasattr(User, "created_at")
        assert hasattr(User, "updated_at")
        assert hasattr(User, "is_deleted")
        assert User.__tablename__ == "users"

    def test_classroom_has_mixins(self):
        from backend.models.classroom import Classroom, ClassroomMembership
        assert hasattr(Classroom, "is_deleted")
        assert hasattr(ClassroomMembership, "is_deleted")

    def test_submission_has_status(self):
        from backend.models.submission import Submission
        assert hasattr(Submission, "status")
        assert hasattr(Submission, "is_deleted")

    def test_text_vector_has_embedding(self):
        from backend.models.text_vector import TextVector
        assert hasattr(TextVector, "embedding")
        assert TextVector.__tablename__ == "text_vectors"

    def test_all_models_export(self):
        from backend.models import (
            Base, User, Classroom, ClassroomMembership,
            AssignmentTask, Submission, TextVector,
        )
        assert all(m is not None for m in [
            Base, User, Classroom, ClassroomMembership,
            AssignmentTask, Submission, TextVector,
        ])


# ─── Schema Layer ───────────────────────────────────────────────────

class TestSchemas:
    def test_signup_validation_passes(self):
        from backend.schemas.auth import SignupRequest
        req = SignupRequest(
            name="Test User",
            email="test@nitj.ac.in",
            password="Password1!",
            role="student",
        )
        assert req.name == "Test User"

    def test_signup_weak_password_fails(self):
        from backend.schemas.auth import SignupRequest
        import pytest
        with pytest.raises(Exception):
            SignupRequest(
                name="Test",
                email="test@nitj.ac.in",
                password="weak",
                role="student",
            )

    def test_signup_invalid_role_fails(self):
        from backend.schemas.auth import SignupRequest
        import pytest
        with pytest.raises(Exception):
            SignupRequest(
                name="Test",
                email="test@nitj.ac.in",
                password="Password1!",
                role="admin",
            )

    def test_verify_otp_schema(self):
        from backend.schemas.auth import VerifyOTPRequest
        req = VerifyOTPRequest(email="test@nitj.ac.in", code="123456")
        assert req.code == "123456"

    def test_verify_otp_short_code_fails(self):
        from backend.schemas.auth import VerifyOTPRequest
        import pytest
        with pytest.raises(Exception):
            VerifyOTPRequest(email="test@nitj.ac.in", code="123")

    def test_classroom_create_schema(self):
        from backend.schemas.classroom import ClassroomCreateRequest
        req = ClassroomCreateRequest(class_name="AI 101")
        assert req.class_name == "AI 101"

    def test_classroom_create_too_short_fails(self):
        from backend.schemas.classroom import ClassroomCreateRequest
        import pytest
        with pytest.raises(Exception):
            ClassroomCreateRequest(class_name="A")

    def test_task_create_schema(self):
        from backend.schemas.classroom import TaskCreateRequest
        req = TaskCreateRequest(title="NLP Research Paper")
        assert req.title == "NLP Research Paper"

    def test_submission_response_schema(self):
        from backend.schemas.submission import SubmissionResponse
        import uuid
        resp = SubmissionResponse(
            message="OK",
            submission_id=uuid.uuid4(),
            plagiarism_score="12.5%",
            matches_found=3,
            sentences_processed=20,
        )
        assert resp.matches_found == 3

    def test_collusion_response_schema(self):
        from backend.schemas.submission import CollusionGroupResponse
        resp = CollusionGroupResponse(total_groups=0, groups=[])
        assert resp.total_groups == 0


# ─── Repository Layer ───────────────────────────────────────────────

class TestRepositories:
    def test_base_repository_import(self):
        from backend.repositories.base import BaseRepository
        assert BaseRepository is not None

    def test_user_repo_inherits_base(self):
        from backend.repositories.user_repo import UserRepository
        from backend.repositories.base import BaseRepository
        assert issubclass(UserRepository, BaseRepository)

    def test_classroom_repo_inherits_base(self):
        from backend.repositories.classroom_repo import ClassroomRepository
        from backend.repositories.base import BaseRepository
        assert issubclass(ClassroomRepository, BaseRepository)

    def test_submission_repo_inherits_base(self):
        from backend.repositories.submission_repo import SubmissionRepository
        from backend.repositories.base import BaseRepository
        assert issubclass(SubmissionRepository, BaseRepository)

    def test_vector_repo_import(self):
        from backend.repositories.vector_repo import VectorRepository
        assert VectorRepository is not None


# ─── Service Layer ──────────────────────────────────────────────────

class TestServices:
    def test_pdf_service_import(self):
        from backend.services.pdf_service import extract_text_from_pdf
        assert callable(extract_text_from_pdf)

    def test_graph_service_import(self):
        from backend.services.graph_service import GraphService
        assert GraphService is not None

    def test_auth_service_import(self):
        from backend.services.auth_service import AuthService
        assert AuthService is not None

    def test_classroom_service_import(self):
        from backend.services.classroom_service import ClassroomService
        assert ClassroomService is not None

    def test_plagiarism_service_import(self):
        from backend.services.plagiarism_service import PlagiarismService
        assert PlagiarismService is not None


# ─── NLP Singleton ──────────────────────────────────────────────────

class TestNLPSingleton:
    def test_singleton_returns_same_instance(self):
        from backend.services.nlp_service import NLPService
        a = NLPService()
        b = NLPService()
        assert a is b

    def test_get_nlp_service_returns_instance(self):
        from backend.services.nlp_service import get_nlp_service
        svc = get_nlp_service()
        assert svc is not None

    def test_get_chunks_returns_tuple(self):
        from backend.services.nlp_service import get_nlp_service
        nlp = get_nlp_service()
        paras, sents = nlp.get_chunks(
            "Hello world. This is a test sentence."
        )
        assert isinstance(paras, list)
        assert isinstance(sents, list)
        assert len(sents) >= 2

    def test_embeddings_dimension(self):
        from backend.services.nlp_service import get_nlp_service
        nlp = get_nlp_service()
        vecs = nlp.generate_embeddings(["test sentence"])
        assert len(vecs) == 1
        assert len(vecs[0]) == 768


# ─── Middleware & App ───────────────────────────────────────────────

class TestAppStructure:
    def test_exception_handler_import(self):
        from backend.middleware.exception_handler import (
            RequestIDMiddleware,
            register_exception_handlers,
        )
        assert callable(register_exception_handlers)
        assert RequestIDMiddleware is not None

    def test_config_loads(self):
        from backend.config import settings
        assert settings.ALGORITHM == "HS256"
        assert settings.SIMILARITY_THRESHOLD == 0.85

    def test_security_functions(self):
        from backend.core.security import hash_password, verify_password
        hashed = hash_password("TestPass1!")
        assert verify_password("TestPass1!", hashed)
        assert not verify_password("wrong", hashed)

    def test_jwt_round_trip(self):
        from backend.core.security import create_access_token, decode_access_token
        token = create_access_token({"sub": "test@nitj.ac.in", "role": "student"})
        payload = decode_access_token(token)
        assert payload["sub"] == "test@nitj.ac.in"
        assert payload["role"] == "student"


# ─── FastAPI App Integration ────────────────────────────────────────

class TestAppRoutes:
    def test_app_creates(self):
        from backend.main import app
        assert app.title == "Assignment Master API"

    def test_v1_routes_registered(self):
        from backend.main import app
        routes = [r.path for r in app.routes]
        assert "/api/v1/auth/signup" in routes
        assert "/api/v1/auth/login" in routes
        assert "/api/v1/classrooms/create" in routes
        assert "/api/v1/classrooms/my" in routes
        assert "/api/v1/assignments/submit/{task_id}" in routes
        assert "/api/v1/assignments/report/{task_id}" in routes
        assert "/api/v1/assignments/matrix/{task_id}" in routes
        assert "/api/v1/assignments/collusion-groups/{task_id}" in routes

    def test_root_endpoint_exists(self):
        from backend.main import app
        routes = [r.path for r in app.routes]
        assert "/" in routes

    def test_health_check(self):
        from fastapi.testclient import TestClient
        from backend.main import app
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "Assignment Master Backend is Online"
