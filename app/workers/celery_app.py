"""Celery application. Models load once per worker process, never inside a task."""

import logging

from celery import Celery
from celery.signals import worker_process_init

from app.common.config import settings
from app.workers.models import image_checker, text_classifier

logger = logging.getLogger(__name__)

celery_app = Celery(
    "scamcheck",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_always_eager=settings.celery_eager,
    task_eager_propagates=False,
    task_time_limit=settings.task_time_limit,
    task_soft_time_limit=max(settings.task_time_limit - 5, 5),
    result_expires=settings.job_ttl_seconds,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)


@worker_process_init.connect
def _load_models(**_kwargs) -> None:
    text_classifier.load()
    image_checker.load()
    logger.info("worker process ready")


if settings.celery_eager:
    text_classifier.load()
    image_checker.load()

import app.workers.tasks  # noqa: E402,F401  registers the tasks
