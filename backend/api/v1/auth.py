"""Authentication routes — signup, verify OTP, login, refresh, password reset."""

from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ...database import get_db
from ...middleware.rate_limiter import limiter
from ...schemas.auth import (
    ForgotPasswordRequest,
    RefreshRequest,
    RefreshResponse,
    ResetPasswordRequest,
    SignupRequest,
    TokenResponse,
    VerifyOTPRequest,
)
from ...schemas.common import MessageResponse
from ...services.auth_service import AuthService

router = APIRouter()


@router.post("/signup", response_model=MessageResponse)
@limiter.limit("5/minute")
async def signup(
    request: Request,
    body: SignupRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    await service.initiate_signup(
        name=body.name,
        email=body.email,
        password=body.password,
        role=body.role,
    )
    return MessageResponse(message="OTP sent successfully")


@router.post("/verify-otp", response_model=MessageResponse)
@limiter.limit("5/minute")
def verify_otp(
    request: Request,
    body: VerifyOTPRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    service.verify_otp(email=body.email, code=body.code)
    return MessageResponse(message="Account activated and saved to database!")


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    result = service.login(email=form_data.username, password=form_data.password)
    return TokenResponse(**result)


@router.post("/refresh", response_model=RefreshResponse)
def refresh_token(
    request: RefreshRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    result = service.refresh_access_token(request.refresh_token)
    return RefreshResponse(**result)


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("5/minute")
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    await service.forgot_password(email=body.email)
    return MessageResponse(
        message="If this email is registered, a reset OTP has been sent."
    )


@router.post("/reset-password", response_model=MessageResponse)
@limiter.limit("5/minute")
def reset_password(
    request: Request,
    body: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    service.reset_password(
        email=body.email,
        code=body.code,
        new_password=body.new_password,
    )
    return MessageResponse(message="Password has been reset successfully.")
