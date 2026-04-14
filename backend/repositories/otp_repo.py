"""Repository for OTP persistence — store, verify, and clean up OTP records."""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from ..models.otp import OTPRecord


class OTPRepository:
    def __init__(self, db: Session):
        self.db = db

    def upsert(self, email: str, code: str, ttl_minutes: int = 5) -> OTPRecord:
        """Store or replace an OTP for the given email."""
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)

        record = self.db.query(OTPRecord).filter(OTPRecord.email == email).first()
        if record:
            record.code = code
            record.expires_at = expires_at
            record.created_at = datetime.now(timezone.utc)
        else:
            record = OTPRecord(email=email, code=code, expires_at=expires_at)
            self.db.add(record)

        self.db.flush()
        return record

    def verify(self, email: str, code: str) -> bool:
        """Check if code matches and hasn't expired. Returns True if valid."""
        record = self.db.query(OTPRecord).filter(OTPRecord.email == email).first()
        if not record:
            return False
        if record.code != code:
            return False
        if record.expires_at < datetime.now(timezone.utc):
            return False
        return True

    def delete(self, email: str) -> None:
        """Remove OTP record after successful verification."""
        self.db.query(OTPRecord).filter(OTPRecord.email == email).delete()
        self.db.flush()
