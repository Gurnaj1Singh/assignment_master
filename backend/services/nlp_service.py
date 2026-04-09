"""
Singleton NLP service wrapping Sentence-Transformers.

The model (~400 MB) is loaded exactly once via double-checked locking.
FastAPI injects it through the get_nlp_service() dependency.
"""

import logging
import threading

import nltk
from sentence_transformers import SentenceTransformer

from ..config import settings

logger = logging.getLogger(__name__)


class NLPService:
    _instance: "NLPService | None" = None
    _lock = threading.Lock()

    def __new__(cls) -> "NLPService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    inst = super().__new__(cls)
                    logger.info(
                        "Loading SBERT model: %s", settings.SBERT_MODEL_NAME
                    )
                    inst._model = SentenceTransformer(settings.SBERT_MODEL_NAME)
                    # Ensure NLTK data is available
                    try:
                        nltk.data.find("tokenizers/punkt_tab")
                    except LookupError:
                        nltk.download("punkt_tab", quiet=True)
                    cls._instance = inst
        return cls._instance

    def get_chunks(self, text: str) -> tuple[list[str], list[str]]:
        """Split text into paragraphs and sentences."""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        sentences = nltk.sent_tokenize(text)
        return paragraphs, sentences

    def generate_embeddings(self, text_list: list[str]) -> list[list[float]]:
        """Convert text list into 768-dimensional vectors."""
        return self._model.encode(text_list).tolist()


# Module-level singleton
_nlp_service: NLPService | None = None
_nlp_lock = threading.Lock()


def get_nlp_service() -> NLPService:
    """FastAPI dependency — returns the singleton NLPService."""
    global _nlp_service
    if _nlp_service is None:
        with _nlp_lock:
            if _nlp_service is None:
                _nlp_service = NLPService()
    return _nlp_service
