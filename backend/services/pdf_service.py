"""PDF text extraction using PyMuPDF (fitz)."""

import logging

import fitz

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract raw text from a PDF file.

    Raises ValueError if the PDF is empty or unreadable, rather than
    silently returning garbage from a binary fallback.
    """
    try:
        text = ""
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text("text") + "\n"
        cleaned = " ".join(text.split())
        if not cleaned:
            raise ValueError("PDF appears to be empty or image-only")
        return cleaned
    except fitz.FileDataError as exc:
        logger.error("Failed to parse PDF %s: %s", file_path, exc)
        raise ValueError(f"Could not read PDF: {exc}") from exc
