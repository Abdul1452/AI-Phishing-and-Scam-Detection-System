from pydantic import BaseModel, Field
from typing import Optional


class SubmitEmailRequest(BaseModel):
    email_text: str = Field(..., min_length=1, max_length=20000)


class SubmitEmailResponse(BaseModel):
    job_id: str
    status: str = "queued"


class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # "queued" | "in_progress" | "completed" | "failed"
    prediction: Optional[str] = None
    confidence: Optional[float] = None
    all_probabilities: Optional[dict] = None
