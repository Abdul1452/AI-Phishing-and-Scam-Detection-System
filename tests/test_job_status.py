from fastapi.testclient import TestClient
import app.api.main as api_main

client = TestClient(api_main.app)


class FakeResult:
    def __init__(self, state, result=None):
        self.state = state
        self._result = result

    def successful(self):
        return self.state == "SUCCESS"

    def failed(self):
        return self.state == "FAILURE"

    @property
    def result(self):
        return self._result


def test_job_status_queued(monkeypatch):
    # AsyncResult returns a PENDING-like object
    import app.workers.celery_app as celery_mod

    monkeypatch.setattr(celery_mod.celery_app, "AsyncResult", lambda job_id: FakeResult(state="PENDING"))

    resp = client.get("/jobs/fake-job")
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] == "fake-job"
    assert data["status"] == "queued"


def test_job_status_running(monkeypatch):
    import app.workers.celery_app as celery_mod

    monkeypatch.setattr(celery_mod.celery_app, "AsyncResult", lambda job_id: FakeResult(state="STARTED"))

    resp = client.get("/jobs/fake-job")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "running"


def test_job_status_failed(monkeypatch):
    import app.workers.celery_app as celery_mod

    monkeypatch.setattr(celery_mod.celery_app, "AsyncResult", lambda job_id: FakeResult(state="FAILURE"))

    resp = client.get("/jobs/fake-job")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "failed"
    assert "error" in data


def test_job_status_completed(monkeypatch):
    import app.workers.celery_app as celery_mod

    payload = {
        "job_id": "fake-job",
        "label": "likely_phishing",
        "score": 0.9,
        "signals": ["ocr:found_url"],
        "caveat": "This is an automated assessment and can be wrong.",
    }
    monkeypatch.setattr(celery_mod.celery_app, "AsyncResult", lambda job_id: FakeResult(state="SUCCESS", result=payload))

    resp = client.get("/jobs/fake-job")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "done"
    assert data["result"]["label"] == "likely_phishing"
    assert abs(data["result"]["score"] - 0.9) < 1e-6
