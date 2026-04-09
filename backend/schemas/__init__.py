from .auth import LoginRequest, SignupRequest, TokenResponse, VerifyOTPRequest
from .classroom import (
    ClassroomCreateRequest,
    ClassroomMemberResponse,
    ClassroomResponse,
    TaskCreateRequest,
    TaskResponse,
)
from .common import ErrorResponse, MessageResponse
from .submission import (
    CollusionGroupResponse,
    PlagiarismMatch,
    ReportEntry,
    SimilarityMatrixEntry,
    SubmissionResponse,
)

__all__ = [
    "SignupRequest",
    "LoginRequest",
    "VerifyOTPRequest",
    "TokenResponse",
    "ClassroomCreateRequest",
    "ClassroomResponse",
    "ClassroomMemberResponse",
    "TaskCreateRequest",
    "TaskResponse",
    "SubmissionResponse",
    "PlagiarismMatch",
    "ReportEntry",
    "SimilarityMatrixEntry",
    "CollusionGroupResponse",
    "MessageResponse",
    "ErrorResponse",
]
