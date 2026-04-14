"""OTP record model — persists OTP codes in the database."""

from sqlalchemy import Column, DateTime, String
from sqlalchemy.sql import func

from .base import Base


class OTPRecord(Base):
    """
    Stores OTP codes for email verification (signup, password reset).

    email      : the target email address (primary key — one active OTP per email).
    code       : 6-digit OTP string.
    expires_at : when this OTP becomes invalid.
    created_at : when this OTP was generated.
    """

    __tablename__ = "otp_records"

    email = Column(String(255), primary_key=True)
    code = Column(String(6), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
