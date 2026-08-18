# Accessibility, ethics, privacy, and limitations

## Accessibility

The upload and submission flow is a browser form and HTTP API. The UI uses file upload controls and form submission in [ui/app.py](../ui/app.py), and the API accepts multipart uploads in [app/api/main.py](../app/api/main.py).

The code does not implement extra accessibility features beyond the standard form controls provided by the framework. The project documentation is not a substitute for a full accessibility audit. This review only covers the upload and guard behaviour that is present in code and tests.

## Ethics and risk handling

The project is a proof-of-concept assessment tool. It does not claim to be a deployable content moderation or security control. The result model in [app/common/schemas.py](../app/common/schemas.py) always includes a caveat string, and the worker tasks return `unclear` results rather than rising exceptions when inference fails.

The image route is explicitly described as a single-frame, low-confidence check in [app/common/schemas.py](../app/common/schemas.py), and the UI warns users that it does not analyse video or audio and has not been evaluated on real-world data. The guard is a rate-limiting aid for repeated submissions, not a claim that an image is safe or malicious.

## Privacy and data handling

The upload path reads the file before queueing it, writes it to a temporary file, and passes the temp path to the Celery worker. The worker reads the file and then deletes it in a `finally` block in [app/workers/tasks.py](../app/workers/tasks.py).

The API does not persist message bodies, image data, or filenames in a database in the code reviewed here. The project README says that submitted text and images are held only for the length of the job and deleted, but the implementation reviewed here shows the worker deletes the temp file after processing and the gateway does not store the content beyond the request handling period.

The guard keeps submission history in memory in [app/api/guards.py](../app/api/guards.py). It stores recent payload values and strike counts keyed by client ID, rather than storing raw filenames or logs. The code does not write message bodies or filenames to logs in the reviewed path.

## Upload validation behaviour

The image route in [app/api/main.py](../app/api/main.py) enforces specific upload checks before enqueuing a job:

- Content-Length is checked before the body is read.
- The request is rejected if the declared size exceeds `settings.max_upload_bytes`.
- The file content is read and checked again after reading.
- Empty uploads are rejected with code `empty_file`.
- MIME validation rejects anything not in `{"image/png", "image/jpeg"}`.
- The route requires a multipart `file` field; a missing file field fails at the framework validation layer with `422`.
- The desired result is a queued job ID for valid uploads.

The tests in [tests/test_image_route.py](../tests/test_image_route.py) and [tests/test_upload.py](../tests/test_upload.py) cover the accepted and rejected cases explicitly: PNG accepted, JPEG accepted, GIF rejected, wrong MIME type rejected, oversized file rejected, empty file rejected, and missing file field rejected.

## Similarity guard behaviour

The guard in [app/api/guards.py](../app/api/guards.py) compares recent submissions for the same client and blocks repeated near-identical inputs after a configured strike threshold. For text inputs, it compares the raw message string; for image inputs, the API computes a SHA256 hash of the file bytes before calling the guard.

The tests in [tests/test_text_route.py](../tests/test_text_route.py) and [tests/test_upload.py](../tests/test_upload.py) verify that:

- repeated near-identical text submissions are blocked
- repeated exact-content image submissions are blocked after the threshold is reached
- different client IDs do not share the same strike counter within a single process

The guard uses a process-local dictionary and a single `threading.Lock` to serialize updates. It is not backed by Redis.

## Limitations

### 1. Exact-content blocking only

The guard blocks repeated exact-content submissions when they land in the same in-memory history for the same client. It does not detect a modified version of the same image or text that is changed enough to avoid the similarity threshold. The code compares a candidate payload to recent values using `rapidfuzz.fuzz.ratio`, and the test coverage is limited to exact-content or near-identical repeated values rather than mutation-resistant detection.

This is the behaviour verified in [app/api/guards.py](../app/api/guards.py) and [tests/test_upload.py](../tests/test_upload.py): the route blocks repeated same-content uploads, not transformed or varied inputs.

### 2. In-memory, per-process state only

The guard stores history in a Python dictionary in memory. This means state does not persist across restarts, and it does not share state across multiple worker processes or multiple API instances. The repository documentation also notes this is a future task to move the guard into Redis with TTL. The code reviewed here does not implement that Redis-backed shared state.

This is a mismatch between the current implementation and any broader claim that the guard is a shared or multi-instance protection mechanism. The code is local to one process only.

### 3. Header-based MIME validation is spoofable

The route checks `file.content_type` against `{"image/png", "image/jpeg"}` and does not inspect file magic bytes. This is a header-based check. A client can lie about `Content-Type`, and the API will accept or reject based on the provided header rather than the file contents. The tests cover header-based validation and supported MIME types, not magic-byte validation.

This means the upload validation is suitable for a simple PoC, but it is not a robust file-type check for untrusted input.

## Documentation mismatch to flag

There is a mismatch between the project’s older wording and the actual implementation in the reviewed code:

- The README and onboarding text refer to a “guard against repeated near-identical submissions,” but the actual image route now checks a SHA256 digest of bytes instead of using the filename or a more general mutation detector.
- The README also says the project is not a deployable security control, but some older wording around scope or protection can read more strongly than the code currently enforces.
- The guard is not Redis-backed in the code reviewed here, even though the onboarding notes mention moving it into Redis as a planned task. The current implementation is in-memory only.

This documentation gap is not resolved by the code here; it is explicitly noted as a limitation of the current prototype.
