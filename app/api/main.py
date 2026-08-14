"""FastAPI gateway. Validates, queues, returns a job ID. Never blocks on inference."""

import logging
import os
import tempfile
import uuid

from fastapi import FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from app.api.guards import ALLOWED_IMAGE_TYPES, similarity_guard
from app.common.config import settings
from app.common.schemas import Assessment, ErrorBody, JobAccepted, JobStatus, TextSubmission

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Phishing and scam assessment", version="0.1.0")


def _fail(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail=ErrorBody(code=code, message=message).model_dump())


def _client_id(request: Request, header: str | None) -> str:
    return header or (request.client.host if request.client else "unknown")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze/text", response_model=JobAccepted, responses={400: {"model": ErrorBody}})
def analyze_text(
    submission: TextSubmission,
    request: Request,
    x_client_id: str | None = Header(default=None),
) -> JobAccepted:
    message = submission.message.strip()
    if len(message) < settings.min_text_chars:
        raise _fail(400, "message_too_short", "Enter a message of at least a few characters.")
    if len(message) > settings.max_text_chars:
        raise _fail(400, "message_too_long", f"Message is longer than {settings.max_text_chars} characters.")
    if similarity_guard.check(_client_id(request, x_client_id), message):
        raise _fail(429, "too_similar", "Too many near-identical submissions. Wait before trying again.")

    from app.workers.tasks import analyze_text as task

    job_id = str(uuid.uuid4())
    task.apply_async(args=[job_id, message], task_id=job_id)
    logger.info("queued text job_id=%s length=%d", job_id, len(message))
    return JobAccepted(job_id=job_id)


@app.post("/analyze/image", response_model=JobAccepted, responses={400: {"model": ErrorBody}})
async def analyze_image(
    request: Request,
    file: UploadFile = File(...),
    x_client_id: str | None = Header(default=None),
) -> JobAccepted:
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise _fail(400, "unsupported_type", "Upload a PNG or JPEG image.")

    declared = request.headers.get("content-length")
    if declared and int(declared) > settings.max_upload_bytes:
        raise _fail(
            413,
            "file_too_large",
            f"File is larger than {settings.max_upload_bytes // (1024 * 1024)} MB, try a smaller image.",
        )

    payload = await file.read(settings.max_upload_bytes + 1)
    if len(payload) == 0:
        raise _fail(400, "empty_file", "The uploaded file is empty.")
    if len(payload) > settings.max_upload_bytes:
        raise _fail(
            413,
            "file_too_large",
            f"File is larger than {settings.max_upload_bytes // (1024 * 1024)} MB, try a smaller image.",
        )

    job_id = str(uuid.uuid4())
    handle, path = tempfile.mkstemp(prefix="upload-", suffix=".bin")
    with os.fdopen(handle, "wb") as out:
        out.write(payload)

    from app.workers.tasks import analyze_image as task

    task.apply_async(args=[job_id, path], task_id=job_id)
    logger.info("queued image job_id=%s bytes=%d", job_id, len(payload))
    return JobAccepted(job_id=job_id)


@app.get("/jobs/{job_id}", response_model=JobStatus)
def job_status(job_id: str) -> JobStatus:
    from app.workers.celery_app import celery_app

    async_result = celery_app.AsyncResult(job_id)
    if async_result.successful():
        return JobStatus(job_id=job_id, status="done", result=Assessment(**async_result.result))
    if async_result.failed():
        return JobStatus(job_id=job_id, status="failed", error="Analysis could not be completed.")
    if async_result.state == "STARTED":
        return JobStatus(job_id=job_id, status="running")
    return JobStatus(job_id=job_id, status="queued")


@app.exception_handler(HTTPException)
def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, dict) else {"code": "error", "message": str(exc.detail)}
    return JSONResponse(status_code=exc.status_code, content=detail)
