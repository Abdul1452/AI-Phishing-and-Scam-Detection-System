---
name: 'API gateway'
description: 'FastAPI gateway rules: validation, queueing, and upload safety'
applyTo: 'app/api/**'
---

# API gateway

This layer validates a request, pushes a task, and returns a job ID. Nothing here
is allowed to be slow.

Do not import `transformers`, `torch`, or anything from `app/workers/`. Shared
types come from `app/common/`. If you need a type that lives in the worker, move
it to `app/common/` rather than importing across the boundary.

Do not call inference, load a model, or `.get()` a Celery result. Submission
returns immediately with a job ID; the client polls a separate status route.

## Routes

Keep them thin. A route validates input, calls one function, and returns a
response model. Business logic that grows past a few lines moves out of the route.

Every route declares an explicit `response_model`. Every route has an error path
that returns a structured body, not a traceback.

## Uploads

Check `content-type` and `content-length` before reading the body. Reject
anything over 10 MB and anything that is not `image/png` or `image/jpeg`. Do not
trust the file extension.

Write to a temporary file with a generated name. Never build a path from a
user-supplied filename, and never pass one to a shell.

Reject empty files and zero-length text submissions with a message saying what to
send instead.

## Similarity middleware

Compare each submission against that client's recent submissions stored in Redis,
using Levenshtein distance. Block after repeated near-identical inputs.

Threshold, window size, and lookback count are configuration, not literals.

Every Redis key this middleware writes gets a TTL. Nothing accumulates.

Write comments that describe what it does: it stops a naive mutation script
hammering one client session. It does not stop an attacker who varies inputs or
rotates sessions. Do not imply otherwise.

## Errors

Error responses carry a machine-readable code and a sentence the UI can display
to a non-technical user. "Upload failed" is not acceptable. "File is larger than
10 MB, try a smaller image" is.