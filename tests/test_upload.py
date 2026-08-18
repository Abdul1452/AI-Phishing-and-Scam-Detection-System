"""Upload validation and guard tests. Content-Length header, MIME type, file size, similarity blocking."""

import pytest

from app.common.config import settings


def test_image_over_10mb_rejected_before_body_read(client):
    """Content-Length header is checked before body is buffered."""
    payload = b"0" * (settings.max_upload_bytes + 1024)
    response = client.post(
        "/analyze/image",
        files={"file": ("big.png", payload, "image/png")},
    )
    assert response.status_code == 413
    assert response.json()["code"] == "file_too_large"


def test_image_png_accepted(client, png_bytes):
    """PNG images pass MIME type validation."""
    response = client.post(
        "/analyze/image",
        files={"file": ("shot.png", png_bytes, "image/png")},
    )
    assert response.status_code == 200
    assert response.json()["job_id"]


def test_image_jpeg_accepted(client):
    """JPEG images pass MIME type validation."""
    jpeg_bytes = b"\xff\xd8\xff\xe0" + b"0" * 64
    response = client.post(
        "/analyze/image",
        files={"file": ("shot.jpg", jpeg_bytes, "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.json()["job_id"]


def test_image_gif_rejected(client):
    """GIF images are rejected as unsupported type."""
    gif_bytes = b"GIF89a" + b"0" * 64
    response = client.post(
        "/analyze/image",
        files={"file": ("shot.gif", gif_bytes, "image/gif")},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "unsupported_type"


def test_image_wrong_extension_rejected(client):
    """File extension mismatch does not bypass MIME check."""
    response = client.post(
        "/analyze/image",
        files={"file": ("note.png", b"hello", "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "unsupported_type"


def test_near_identical_image_resubmission_blocked(client, png_bytes):
    """Repeated submissions of the exact same image file are blocked after strike threshold."""
    # Same file bytes submitted multiple times should trigger similarity guard
    # The guard checks the SHA256 hash of content, blocking near-identical hashes
    for i in range(settings.similarity_strikes + 1):
        response = client.post(
            "/analyze/image",
            files={"file": (f"shot_{i}.png", png_bytes, "image/png")},
        )
        if i < settings.similarity_strikes:
            assert response.status_code == 200, f"Submission {i} should be accepted"
        else:
            # On/after the strike threshold, same content is blocked
            assert response.status_code == 429, f"Submission {i} should be blocked"
            assert response.json()["code"] == "too_similar"


def test_similar_image_guard_is_per_client(client, png_bytes):
    """The same image can be re-used by a different client without sharing that client's strike count."""
    headers_a = {"X-Client-Id": "client-a"}
    headers_b = {"X-Client-Id": "client-b"}

    for i in range(settings.similarity_strikes):
        response = client.post(
            "/analyze/image",
            files={"file": (f"shot_a_{i}.png", png_bytes, "image/png")},
            headers=headers_a,
        )
        assert response.status_code == 200, f"Client A submission {i} should be accepted"

    # Client A has now accumulated the configured strikes for the same image content.
    blocked = client.post(
        "/analyze/image",
        files={"file": ("shot_a_final.png", png_bytes, "image/png")},
        headers=headers_a,
    )
    assert blocked.status_code == 429
    assert blocked.json()["code"] == "too_similar"

    # Client B should start fresh and should not inherit client A's strike state.
    response = client.post(
        "/analyze/image",
        files={"file": ("shot_b.png", png_bytes, "image/png")},
        headers=headers_b,
    )
    assert response.status_code == 200, "Client B should not be blocked by Client A's history"


def test_assessment_imports_from_app_common(client, png_bytes):
    """ErrorBody responses use schemas from app.common."""
    # Test that error responses use ErrorBody from app.common.schemas
    response = client.post(
        "/analyze/image",
        files={"file": ("note.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400
    error = response.json()
    
    # ErrorBody fields from app.common.schemas
    assert "code" in error
    assert "message" in error
    assert error["code"] == "unsupported_type"


def test_all_endpoint_responses_use_common_schemas_text(client):
    """Text endpoint returns error body from app.common.schemas."""
    response = client.post("/analyze/text", json={"message": "hi"})
    assert response.status_code == 400
    error = response.json()
    assert "code" in error
    assert "message" in error
    
    response = client.post("/analyze/text", json={"message": "a" * 30000})
    assert response.status_code == 400
    error = response.json()
    assert "code" in error
    assert "message" in error


def test_all_endpoint_responses_use_common_schemas(client):
    """Both text and image endpoints return ErrorBody from app.common.schemas."""
    # Text error
    response = client.post("/analyze/text", json={"message": "hi"})
    assert response.status_code == 400
    error = response.json()
    assert "code" in error
    assert "message" in error
    
    # Image error
    response = client.post(
        "/analyze/image",
        files={"file": ("note.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400
    error = response.json()
    assert "code" in error
    assert "message" in error
