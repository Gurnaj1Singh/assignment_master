"""Authentication routes — signup, verify OTP, login."""

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ...database import get_db
from ...schemas.auth import SignupRequest, TokenResponse, VerifyOTPRequest
from ...schemas.common import MessageResponse
from ...services.auth_service import AuthService

router = APIRouter()


@router.post("/signup", response_model=MessageResponse)
async def signup(
    request: SignupRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    await service.initiate_signup(
        name=request.name,
        email=request.email,
        password=request.password,
        role=request.role,
    )
    return MessageResponse(message="OTP sent successfully")


@router.post("/verify-otp", response_model=MessageResponse)
def verify_otp(
    request: VerifyOTPRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    service.verify_otp(email=request.email, code=request.code)
    return MessageResponse(message="Account activated and saved to database!")


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    result = service.login(email=form_data.username, password=form_data.password)
    return TokenResponse(**result)
