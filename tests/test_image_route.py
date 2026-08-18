from app.common.config import settings


def test_wrong_content_type_rejected(client):
    response = client.post("/analyze/image", files={"file": ("note.txt", b"hello", "text/plain")})
    assert response.status_code == 400
    assert response.json()["code"] == "unsupported_type"


def test_renamed_text_file_still_rejected_by_type(client):
    response = client.post("/analyze/image", files={"file": ("note.png", b"hello", "text/plain")})
    assert response.status_code == 400


def test_empty_file_rejected(client, png_bytes):
    response = client.post("/analyze/image", files={"file": ("shot.png", b"", "image/png")})
    assert response.status_code == 400
    assert response.json()["code"] == "empty_file"


def test_missing_file_field_rejected(client):
    response = client.post("/analyze/image", files={})
    assert response.status_code == 422


def test_oversized_file_rejected(client):
    payload = b"0" * (settings.max_upload_bytes + 1024)
    response = client.post("/analyze/image", files={"file": ("big.png", payload, "image/png")})
    assert response.status_code == 413


def test_valid_image_accepted(client, png_bytes):
    response = client.post("/analyze/image", files={"file": ("shot.png", png_bytes, "image/png")})
    assert response.status_code == 200
    assert response.json()["job_id"]
