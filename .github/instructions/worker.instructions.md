---
name: 'Celery worker'
description: 'Worker rules: model lifecycle, cleanup, and result construction'
applyTo: 'app/workers/**'
---

# Celery worker

All inference happens here. This layer is allowed to be slow, but only after
startup.

## Model lifecycle

Models load once when the worker process starts, at module level or in a
`worker_process_init` handler. Never inside a task body. A per-request load will
make the first demo submission look like a hang.

Wrap each model behind a small class with one `predict` method taking plain
Python types and returning plain Python types. Tests mock at that class, so no
`transformers` call belongs anywhere else.

Pin model IDs in configuration, not in the task. Download during image build so
the container starts offline.

If a model fails to load, fail loudly at startup rather than at first request.

## Tasks

A task takes a job ID and primitives. It does not take file handles, request
objects, or Pydantic models that are expensive to serialise.

Set a hard time limit on every task. A task that exceeds it returns an unclear
result with a caveat explaining the timeout, rather than leaving the UI polling
forever.

Catch inference errors and return an `Assessment` with the `unclear` label. A
traceback reaching the UI is a demo failure.

## Results

Construct an `Assessment` with a job ID, a label, a score between 0 and 1, a list
of human-readable signals, and a caveat. The caveat is always populated. There is
no code path that returns a result without one.

Signals say what the model reacted to in plain language, for example urgency
phrasing or a mismatched link domain. They are not raw feature weights.

The image check is single-frame and low confidence. Its caveat says so explicitly.

Never use verdict, proof, confirmed, safe, or guaranteed. Use assessment,
indicator, score, or likely.

## Cleanup

Delete every temporary file in a `finally` block, including on failure.

Every Redis key the worker writes has a TTL of 15 minutes. Submitted text and
images are never written to persistent storage.