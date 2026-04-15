"""Authentication business logic — OTP management, user creation, login."""

import logging
import secrets

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..core.email import send_otp_email, validate_nitj_email
from ..core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from ..models.user import User
from ..repositories.otp_repo import OTPRepository
from ..repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)

# Temporary store for signup data between OTP send and verification.
# Only holds pre-registration data (name, password_hash, role) until the
# OTP is verified and the user row is created. Not security-critical —
# the OTP itself is now persisted in the DB.
_user_data_store: dict[str, dict] = {}


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.otp_repo = OTPRepository(db)

    async def initiate_signup(
        self, name: str, email: str, password: str, role: str
    ) -> str:
        email = email.lower()

        if self.user_repo.get_by_email(email):
            raise HTTPException(status_code=400, detail="Email already registered")

        if not validate_nitj_email(email):
            raise HTTPException(
                status_code=400, detail="Only @nitj.ac.in allowed"
            )

        otp = f"{secrets.randbelow(1_000_000):06d}"

        # Persist OTP in database (5-minute TTL)
        self.otp_repo.upsert(email, otp, ttl_minutes=5)
        self.db.commit()

        _user_data_store[email] = {
            "name": name,
            "password_hash": hash_password(password),
            "role": role,
        }

        try:
            await send_otp_email(email, otp, purpose="signup")
        except Exception:
            logger.exception("SMTP failure during signup for %s", email)
            raise HTTPException(
                status_code=502,
                detail="Unable to send verification email. Please try again later.",
            )
        return otp

    def verify_otp(self, email: str, code: str) -> User:
        email = email.lower()

        if not self.otp_repo.verify(email, code):
            raise HTTPException(
                status_code=400, detail="Invalid or expired OTP."
            )

        data = _user_data_store.get(email)
        if not data:
            raise HTTPException(status_code=400, detail="User data expired.")

        new_user = self.user_repo.create(
            name=data["name"],
            email=email,
            password_hash=data["password_hash"],
            role=data["role"],
        )

        # Clean up OTP record and temp data
        self.otp_repo.delete(email)
        self.db.commit()
        _user_data_store.pop(email, None)

        return new_user

    def login(self, email: str, password: str) -> dict:
        email = email.lower()
        user = self.user_repo.get_by_email(email)

        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = create_access_token(
            data={
                "sub": user.email,
                "role": user.role,
                "user_id": str(user.id),
            }
        )
        refresh_token = create_refresh_token(
            data={"sub": user.email, "user_id": str(user.id)}
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "role": user.role,
        }

    def refresh_access_token(self, refresh_token: str) -> dict:
        """Validate a refresh token and issue a new access token."""
        payload = decode_refresh_token(refresh_token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        user = self.user_repo.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        new_access_token = create_access_token(
            data={
                "sub": user.email,
                "role": user.role,
                "user_id": str(user.id),
            }
        )

        return {
            "access_token": new_access_token,
            "token_type": "bearer",
        }

    async def forgot_password(self, email: str) -> None:
        """Send a password-reset OTP to the user's email."""
        email = email.lower()
        user = self.user_repo.get_by_email(email)
        if not user:
            # Don't reveal whether the email exists
            logger.info("Forgot-password request for unknown email: %s", email)
            return

        otp = f"{secrets.randbelow(1_000_000):06d}"
        self.otp_repo.upsert(email, otp, ttl_minutes=5)
        self.db.commit()

        try:
            await send_otp_email(email, otp, purpose="reset")
        except Exception:
            logger.exception("SMTP failure during forgot-password for %s", email)
            raise HTTPException(
                status_code=502,
                detail="Unable to send reset email. Please try again later.",
            )

    def reset_password(self, email: str, code: str, new_password: str) -> None:
        """Verify OTP and set a new password."""
        email = email.lower()

        if not self.otp_repo.verify(email, code):
            raise HTTPException(
                status_code=400, detail="Invalid or expired OTP."
            )

        user = self.user_repo.get_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        user.password_hash = hash_password(new_password)
        self.otp_repo.delete(email)
        self.db.commit()
