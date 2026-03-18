import fitz  # PyMuPDF
from typing import List
from fastapi_mail import FastMail, MessageSchema, MessageType
from .config import conf
import os

# Your existing NITJ validator
def validate_nitj_email(email: str) -> bool:
    return email.endswith("@nitj.ac.in")

async def send_otp_email(email_to: str, otp: str):
    print(f"\n[DEMO DEBUG] OTP for {email_to} is: {otp}\n")
    """
    Dynamically sends an OTP to the specific user signing up.
    """
    html = f"""
    <html>
        <body>
            <p>Hi,</p>
            <p>Thank you for registering for <b>Assignment Master</b>.</p>
            <p>Your verification code is: <b>{otp}</b></p>
            <p>This code will expire in 10 minutes.</p>
        </body>
    </html>
    """

    message = MessageSchema(
        subject="Assignment Master Verification Code",
        recipients=[email_to], # This is dynamic!
        body=html,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts raw text from a PDF file using PyMuPDF.
    """
    text = ""
    try:
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text("text") + "\n"
        return " ".join(text.split()) # Cleans up extra whitespace/newlines
    except Exception as e:
        with open(file_path, "r", errors="ignore") as f:
            return f.read()
