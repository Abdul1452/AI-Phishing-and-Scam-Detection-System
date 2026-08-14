"""Types crossing an HTTP or queue boundary. Shared by the gateway and the worker."""

from typing import Literal

from pydantic import BaseModel, Field

Label = Literal["likely_phishing", "unclear", "likely_legitimate"]

TEXT_CAVEAT = (
    "This is an automated assessment and can be wrong in both directions. "
    "Treat it as one signal, not proof, and apply your own judgement."
)

IMAGE_CAVEAT = (
    "Low confidence. This is a single-image check only, not video or audio "
    "analysis, and it has not been evaluated on real-world data."
)


class Assessment(BaseModel):
    """The only shape a detection result is allowed to take."""

    job_id: str
    label: Label
    score: float = Field(ge=0.0, le=1.0)
    signals: list[str] = Field(default_factory=list)
    caveat: str = Field(min_length=1)


class TextSubmission(BaseModel):
    message: str


class JobAccepted(BaseModel):
    job_id: str
    status: Literal["queued"] = "queued"


class JobStatus(BaseModel):
    job_id: str
    status: Literal["queued", "running", "done", "failed"]
    result: Assessment | None = None
    error: str | None = None


class ErrorBody(BaseModel):
    code: str
    message: str
