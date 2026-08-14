from app.common.config import settings


def test_short_message_rejected(client):
    response = client.post("/analyze/text", json={"message": "hi"})
    assert response.status_code == 400
    assert response.json()["code"] == "message_too_short"


def test_long_message_rejected(client):
    response = client.post("/analyze/text", json={"message": "a" * (settings.max_text_chars + 1)})
    assert response.status_code == 400


def test_missing_field_rejected(client):
    assert client.post("/analyze/text", json={}).status_code == 422


def test_submission_returns_job_id(client):
    response = client.post("/analyze/text", json={"message": "Please verify your account urgently"})
    assert response.status_code == 200
    assert response.json()["status"] == "queued"
    assert response.json()["job_id"]


def test_repeated_near_identical_submissions_blocked(client):
    body = {"message": "Urgent: verify your account or it will be suspended today"}
    for _ in range(4):
        last = client.post("/analyze/text", json=body)
    assert last.status_code == 429
    assert last.json()["code"] == "too_similar"
