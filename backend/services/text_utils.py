"""Text comparison utilities for plagiarism detection."""

import re
from difflib import SequenceMatcher


def _normalize(text: str) -> str:
    """Lowercase, strip whitespace, remove punctuation."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def is_verbatim(text_a: str, text_b: str, threshold: float = 0.95) -> bool:
    """
    Return True if two strings are near-exact copies after normalization.

    Uses difflib.SequenceMatcher ratio (0.0 to 1.0).
    Default threshold 0.95 catches minor whitespace / punctuation differences.
    """
    norm_a = _normalize(text_a)
    norm_b = _normalize(text_b)
    return SequenceMatcher(None, norm_a, norm_b).ratio() > threshold
