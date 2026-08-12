# Project instructions

## What this project is

A proof-of-concept web application that screens text messages for phishing
indicators and images for signs of manipulation.

This is a prototype for a live demo, not a production security tool. Prefer the
smaller working version over the more capable broken one. If a change would take
more than a few hours to get running, say so instead of starting it.

## Scope

In scope:

- Text phishing classification using a pretrained Hugging Face model.
- Single-image manipulation check, clearly labelled in the UI as low confidence.
- Async job submission through a queue, with a job ID and polling.
- Repeated-submission detection using Levenshtein distance in Redis.

Out of scope. Do not scaffold, stub, or add dependencies for these:

- Video or audio analysis.
- Multi-frame facial consistency.
- Model training or fine-tuning.
- User accounts, authentication, or a database.
- Kubernetes, cloud deployment, CI beyond a test run.

## Stack

Python 3.11. FastAPI for the gateway, Celery with a Redis broker for the queue,
Streamlit for the UI, Docker Compose to run all four containers. Hugging Face
`transformers` for inference, `pytest` for tests.

Do not introduce a new library without a reason that a reviewer would accept.
The standard library is usually enough.

## Architecture

Four services: `ui` (Streamlit), `api` (FastAPI), `redis`, `worker` (Celery).

The gateway never loads a model and never blocks on inference. It validates the
request, pushes a task, and returns a job ID. Anything slow happens in the
worker.

Models load once when the worker process starts, not on each task. A cold load
per request will make the demo look broken.

The UI talks only to the API over HTTP. It does not import worker code, connect
to Redis, or call `transformers`.

Layout:

```
app/
  api/          FastAPI routes and request/response models
  workers/      Celery tasks and model wrappers
  common/       schemas and config shared by both
ui/             Streamlit app
tests/
```

Nothing in `app/api/` imports from `app/workers/`. Shared types go in
`app/common/`.

## Code style

Type hints on every function. Pydantic models for anything crossing an HTTP or
queue boundary, never bare dicts.

Format with `black`, lint with `ruff`, line length 100.

No bare `except:`. Catch the specific exception, log it with the job ID, and
return a structured error the UI can display.

Use the `logging` module, never `print`. Log the job ID, the input length, and a
hash of the input. Never log the message body or a filename a user supplied.

All configuration comes from environment variables with a default suitable for
Docker Compose. No hardcoded `redis://localhost`, no secrets in the repository,
no API keys in committed files.

## How to describe results

The models are wrong sometimes in both directions. Language in code, API
responses, and UI text has to reflect that.

Never use the words verdict, proof, confirmed, safe, or guaranteed about a
result. Use assessment, indicator, score, or likely.

Every result carries a numeric score, a label, and a caveat string:

```python
class Assessment(BaseModel):
    job_id: str
    label: Literal["likely_phishing", "unclear", "likely_legitimate"]
    score: float          # 0.0-1.0
    signals: list[str]    # human-readable reasons
    caveat: str           # shown next to the result in the UI
```

The UI always displays the caveat. Do not add a code path that hides it.

## Security

Check content type and size before reading an upload. Cap uploads at 10 MB and
reject anything that is not `image/png` or `image/jpeg`.

Never pass user input to `eval`, `exec`, a shell, or a filesystem path. Write
uploads to a temporary file with a generated name and delete it once the task
finishes.

The similarity middleware compares each submission against that client's recent
submissions held in Redis and blocks after repeated near-identical inputs. Write
it so the threshold and window are configurable. It catches a naive mutation
script and not much else; do not write comments claiming otherwise.

## Privacy

Submitted text and images are held only as long as the job needs them. Set a
Redis TTL of 15 minutes on job data and delete uploaded files after processing.
Nothing about a submission is written to disk permanently.

## Accessibility

Every input has a visible label, not placeholder text doing the job of a label.

Never signal a result by colour alone. Pair every colour with text and a shape or
icon, so the result is readable in greyscale.

Error messages say what went wrong and what to do next. "Upload failed" is not
acceptable; "File is larger than 10 MB, try a smaller image" is.

Text and background contrast at least 4.5:1.

The whole flow works from the keyboard.

## Tests

`pytest`. Mock model inference; tests must never download a model or hit the
network. Run Celery in eager mode to test the submit-to-result path in process.

Every route needs a test for the rejection cases, not only the happy path.

## Things not to do

Do not add services, containers, or infrastructure that is not already listed
above.

Do not invent MITRE ATT&CK technique identifiers. T1598 is the only one this
project claims. If a mapping seems to fit, flag it rather than writing it in.

Do not state accuracy, precision, or detection rates anywhere. Nothing has been
measured yet.

Do not edit files outside the ones a task asks for, and do not reformat a file
you are only reading.

Do not silently drop a requirement because it is hard. Say it is hard.