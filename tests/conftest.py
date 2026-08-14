import os

os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "1")
os.environ.setdefault("CELERY_BROKER_URL", "memory://")
os.environ.setdefault("CELERY_RESULT_BACKEND", "cache+memory://")

import pytest
from fastapi.testclient import TestClient

from app.api.guards import similarity_guard
from app.api.main import app


@pytest.fixture()
def client() -> TestClient:
    similarity_guard.reset()
    return TestClient(app)


@pytest.fixture()
def png_bytes() -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"0" * 64
