import pytest
from pydantic import ValidationError

from app.common.schemas import TEXT_CAVEAT, Assessment
from app.workers.tasks import analyze_text


def test_every_result_carries_a_caveat():
    """This test keeps an ethics claim honest. Do not delete it to make a refactor pass."""
    result = analyze_text.run("job-1", "Urgent: click here to verify your password")
    assert Assessment(**result).caveat.strip()


def test_assessment_rejects_empty_caveat():
    with pytest.raises(ValidationError):
        Assessment(job_id="j", label="unclear", score=0.5, signals=[], caveat="")


def test_assessment_rejects_out_of_range_score():
    with pytest.raises(ValidationError):
        Assessment(job_id="j", label="unclear", score=1.4, signals=[], caveat=TEXT_CAVEAT)


def test_failure_returns_unclear_not_an_exception(monkeypatch):
    from app.workers import models

    monkeypatch.setattr(
        models.text_classifier, "predict", lambda _m: (_ for _ in ()).throw(RuntimeError("boom"))
    )
    result = Assessment(**analyze_text.run("job-2", "anything"))
    assert result.label == "unclear"
    assert result.caveat
