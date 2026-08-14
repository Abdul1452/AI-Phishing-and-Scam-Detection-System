# AI-Phishing-and-Scam-Detection-System
Detects phishing emails and scam messages using natural language processing. Includes a deepfake detection tool that analyzes images, audio, or video for signs of AI-generated manipulation.

# Phishing and scam assessment

A proof of concept that screens message text for phishing indicators and images
for signs of manipulation. Submissions are queued and analysed in the background,
so the interface stays responsive while inference runs.

Built for the Turku UAS summer school course *Secure, Accessible and Efficient
AI-Assisted Software Development*, August 2026. This is a prototype for a live
demo, not a deployable security control.

## Running it

You need Docker Desktop. Nothing else.

```bash
git clone <repo-url>
cd <repo>
cp .env.example .env
docker compose up --build
```

Open http://localhost:8501 for the interface and http://localhost:8000/docs for
the API.

The first build takes a few minutes. After that, `docker compose up` is seconds.

## Running the tests

Tests run offline with inference mocked, so you do not need containers.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
make test
```

Fourteen tests should pass. If they do not, fix that before writing anything new.

## What is wired up and what is not

Working now: all four services, submission and polling, upload and text
validation, the repeated-submission guard, result rendering with a caveat, and
the test suite.

Stubbed, waiting for someone to replace: the bodies of `TextClassifier.predict`
and `ImageChecker.predict` in `app/workers/models.py`. Both return plausible
results so the pipeline is demonstrable end to end. Swapping in a real Hugging
Face pipeline touches that one file and nothing else.

Also pending: moving the similarity guard's history into Redis with a TTL, and
switching it from `difflib` to a real Levenshtein ratio.

## Layout

```
app/api/        FastAPI gateway: validation, queueing, job status
app/workers/    Celery tasks and model wrappers
app/common/     config and schemas shared by both
ui/             Streamlit interface
tests/          pytest, offline, inference mocked
samples/        demo inputs, committed
.github/        instructions, agents, and prompt files for Copilot
```

Nothing in `app/api/` imports from `app/workers/`. The UI reaches the API over
HTTP and nothing else.

## Scope

In: text phishing classification, a single-image manipulation check, async
processing with job IDs, and a guard against repeated near-identical submissions.

Out, and staying out: video, audio, multi-frame facial consistency, model
training, user accounts, and any database.

## Working with Copilot on this repo

Read `ONBOARDING.md` before your first prompt. The short version: the repository
carries its own instructions, five task agents, and a `/demo-check` command. Pick
the agent that matches what you are doing rather than prompting the default.

## Limitations

Detection results are assessments that can be wrong in both directions, not
proof. Quality varies across languages, writing styles, image quality, and
cultural context, and none of that has been measured. The image check is
single-frame and low confidence. The submission guard stops a naive mutation
script against one client session and nothing more sophisticated than that.

Submitted text and images are held for the length of the job and deleted. No
message bodies or filenames are written to logs.