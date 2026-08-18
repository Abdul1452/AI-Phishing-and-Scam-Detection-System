"""Central configuration. Every environment variable the project reads lives here."""

import os
from dataclasses import dataclass


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    celery_broker_url: str = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    celery_result_backend: str = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")
    api_base_url: str = os.getenv("API_BASE_URL", "http://api:8000")

    text_model_id: str = os.getenv("TEXT_MODEL_ID", "ElSlay/BERT-Phishing-Email-Model")
    image_model_id: str = os.getenv("IMAGE_MODEL_ID", "")

    max_upload_bytes: int = _int("MAX_UPLOAD_BYTES", 10 * 1024 * 1024)
    max_text_chars: int = _int("MAX_TEXT_CHARS", 20_000)
    min_text_chars: int = _int("MIN_TEXT_CHARS", 3)
    job_ttl_seconds: int = _int("JOB_TTL_SECONDS", 900)
    task_time_limit: int = _int("TASK_TIME_LIMIT", 60)

    similarity_threshold: float = _float("SIMILARITY_THRESHOLD", 0.92)
    similarity_window: int = _int("SIMILARITY_WINDOW", 8)
    similarity_strikes: int = _int("SIMILARITY_STRIKES", 3)

    celery_eager: bool = os.getenv("CELERY_TASK_ALWAYS_EAGER", "0") == "1"


settings = Settings()
