from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from celery.result import AsyncResult

from app.workers.celery_app import celery_app
from app.workers.tasks import analyze_email_task
from app.api.schemas import SubmitEmailRequest, SubmitEmailResponse, JobStatusResponse

app = FastAPI(title="AI Phishing & Scam Detection", version="0.1.0")

# Loosen for local dev; tighten before any real deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/analyze", response_model=SubmitEmailResponse)
def submit_email(payload: SubmitEmailRequest):
    """Enqueue an email for phishing analysis. Returns immediately with a job ID."""
    task = analyze_email_task.delay(payload.email_text)
    return SubmitEmailResponse(job_id=task.id, status="queued")


@app.get("/api/analyze/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str):
    """Poll this with the job_id returned from /api/analyze."""
    result = AsyncResult(job_id, app=celery_app)

    if result.state == "PENDING":
        return JobStatusResponse(job_id=job_id, status="queued")
    elif result.state == "STARTED":
        return JobStatusResponse(job_id=job_id, status="in_progress")
    elif result.state == "SUCCESS":
        data = result.result
        return JobStatusResponse(
            job_id=job_id,
            status="completed",
            prediction=data["prediction"],
            confidence=data["confidence"],
            all_probabilities=data["all_probabilities"],
        )
    elif result.state == "FAILURE":
        return JobStatusResponse(job_id=job_id, status="failed")
    else:
        return JobStatusResponse(job_id=job_id, status=result.state.lower())
