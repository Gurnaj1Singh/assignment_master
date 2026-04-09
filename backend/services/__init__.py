from .auth_service import AuthService
from .classroom_service import ClassroomService
from .graph_service import GraphService
from .nlp_service import NLPService, get_nlp_service
from .pdf_service import extract_text_from_pdf
from .plagiarism_service import PlagiarismService

__all__ = [
    "AuthService",
    "ClassroomService",
    "NLPService",
    "get_nlp_service",
    "PlagiarismService",
    "extract_text_from_pdf",
    "GraphService",
]
