"""Email utilities for OTP delivery."""

import logging

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from ..config import settings

logger = logging.getLogger(__name__)

mail_conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=True,
)


def validate_nitj_email(email: str) -> bool:
    """Restricts registration to NITJ domain."""
    return email.endswith("@nitj.ac.in")


async def send_otp_email(email_to: str, otp: str) -> None:
    """Send OTP verification email."""
    logger.info("Sending OTP to %s", email_to)

    html = f"""
    <html><body>
        <p>Hi,</p>
        <p>Thank you for registering for <b>Assignment Master</b>.</p>
        <p>Your verification code is: <b>{otp}</b></p>
        <p>This code will expire in 10 minutes.</p>
    </body></html>
    """

    message = MessageSchema(
        subject="Assignment Master Verification Code",
        recipients=[email_to],
        body=html,
        subtype=MessageType.html,
    )

    fm = FastMail(mail_conf)
    await fm.send_message(message)
