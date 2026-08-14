"""Celery tasks. Take primitives, return a serialised Assessment, never raise upward."""

import logging
import os
from typing import Any

from celery.exceptions import SoftTimeLimitExceeded

from app.common.schemas import IMAGE_CAVEAT, TEXT_CAVEAT, Assessment
from app.workers.celery_app import celery_app
from app.workers.models import image_checker, text_classifier

logger = logging.getLogger(__name__)


def _label(score: float) -> str:
    if score >= 0.66:
        return "likely_phishing"
    if score <= 0.33:
        return "likely_legitimate"
    return "unclear"


def _unclear(job_id: str, reason: str, caveat: str) -> dict[str, Any]:
    return Assessment(
        job_id=job_id, label="unclear", score=0.5, signals=[reason], caveat=caveat
    ).model_dump()


@celery_app.task(name="analyze_text")
def analyze_text(job_id: str, message: str) -> dict[str, Any]:
    logger.info("analyze_text job_id=%s length=%d", job_id, len(message))
    try:
        score, signals = text_classifier.predict(message)
    except SoftTimeLimitExceeded:
        return _unclear(job_id, "analysis timed out", TEXT_CAVEAT)
    except Exception:
        logger.exception("analyze_text failed job_id=%s", job_id)
        return _unclear(job_id, "analysis could not be completed", TEXT_CAVEAT)
    return Assessment(
        job_id=job_id,
        label=_label(score),
        score=score,
        signals=signals or ["no strong indicators found"],
        caveat=TEXT_CAVEAT,
    ).model_dump()


@celery_app.task(name="analyze_image")
def analyze_image(job_id: str, path: str) -> dict[str, Any]:
    logger.info("analyze_image job_id=%s", job_id)
    try:
        with open(path, "rb") as handle:
            payload = handle.read()
        score, signals = image_checker.predict(payload)
    except SoftTimeLimitExceeded:
        return _unclear(job_id, "analysis timed out", IMAGE_CAVEAT)
    except Exception:
        logger.exception("analyze_image failed job_id=%s", job_id)
        return _unclear(job_id, "analysis could not be completed", IMAGE_CAVEAT)
    finally:
        try:
            os.remove(path)
        except OSError:
            logger.warning("temp file already gone job_id=%s", job_id)
    return Assessment(
        job_id=job_id,
        label=_label(score),
        score=score,
        signals=signals,
        caveat=IMAGE_CAVEAT,
    ).model_dump()
