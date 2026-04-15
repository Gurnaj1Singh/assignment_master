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


async def send_otp_email(
    email_to: str, otp: str, purpose: str = "signup"
) -> None:
    """Send OTP verification email.

    Args:
        email_to: Recipient address.
        otp: The 6-digit code.
        purpose: Either "signup" or "reset" — controls email copy.
    """
    logger.info("Sending %s OTP to %s", purpose, email_to)

    if purpose == "reset":
        subject = "Assignment Master — Password Reset Code"
        html = f"""
        <html><body>
            <p>Hi,</p>
            <p>We received a request to reset your <b>Assignment Master</b> password.</p>
            <p>Your password-reset code is: <b>{otp}</b></p>
            <p>This code will expire in <b>5 minutes</b>.</p>
            <p>If you did not request this, you can safely ignore this email.</p>
        </body></html>
        """
    else:
        subject = "Assignment Master — Verification Code"
        html = f"""
        <html><body>
            <p>Hi,</p>
            <p>Thank you for registering for <b>Assignment Master</b>.</p>
            <p>Your verification code is: <b>{otp}</b></p>
            <p>This code will expire in <b>5 minutes</b>.</p>
        </body></html>
        """

    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=html,
        subtype=MessageType.html,
    )

    try:
        fm = FastMail(mail_conf)
        await fm.send_message(message)
        logger.info("OTP email sent successfully to %s", email_to)
    except Exception:
        logger.exception("Failed to send OTP email to %s", email_to)
        raise
