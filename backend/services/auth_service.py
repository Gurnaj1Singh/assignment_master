"""Authentication business logic — OTP management, user creation, login."""

import logging
import random
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..core.email import send_otp_email, validate_nitj_email
from ..core.security import create_access_token, hash_password, verify_password
from ..models.user import User
from ..repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)

# In-memory OTP store — migrate to Redis for multi-worker production
_otp_store: dict[str, str] = {}
_user_data_store: dict[str, dict] = {}


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

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

        otp = str(random.randint(100000, 999999))
        _otp_store[email] = otp
        _user_data_store[email] = {
            "name": name,
            "password_hash": hash_password(password),
            "role": role,
        }

        await send_otp_email(email, otp)
        return otp

    def verify_otp(self, email: str, code: str) -> User:
        email = email.lower()

        if _otp_store.get(email) != code:
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
        self.db.commit()

        _otp_store.pop(email, None)
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

        token = create_access_token(
            data={
                "sub": user.email,
                "role": user.role,
                "user_id": str(user.id),
            }
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "role": user.role,
        }
