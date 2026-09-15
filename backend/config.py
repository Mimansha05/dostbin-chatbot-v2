import logging
import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)

logger = logging.getLogger("dostbin")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = (
    os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip()
    or "openai/gpt-oss-120b"
)
GROQ_BASE_URL = (
    os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").strip()
    or "https://api.groq.com/openai/v1"
)
GROQ_TIMEOUT_SECONDS = float(os.getenv("GROQ_TIMEOUT_SECONDS", "45"))
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:8000,http://127.0.0.1:8000",
    ).split(",")
    if origin.strip()
]
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "30"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
MAX_QUESTION_LENGTH = int(os.getenv("MAX_QUESTION_LENGTH", "500"))


def groq_configured():
    return bool(GROQ_API_KEY)


def validate_startup():
    if not GROQ_API_KEY:
        logger.warning(
            "GROQ_API_KEY is not set. Chat endpoints will return 503 until it is configured."
        )
    return {
        "groq_configured": groq_configured(),
        "model": GROQ_MODEL,
        "base_url": GROQ_BASE_URL,
    }
