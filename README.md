# AI Phishing & Scam Detection — PoC

## Prerequisites
- Python 3.10+
- Redis running locally (`redis-server`)

## Setup
```bash
pip install -r requirements.txt
```

## Run (3 separate terminals, from the project root)

**Terminal 1 — Redis** (skip if already running)
```bash
redis-server
```

**Terminal 2 — Celery worker**
```bash
celery -A app.workers.celery_app worker --loglevel=info --pool=solo
```
First startup will download the BERT model (~420MB) — this is slow once,
then cached. Wait for `celery@... ready.` before moving on.

**Terminal 3 — FastAPI gateway**
```bash
uvicorn app.main:app --reload --port 8000
```
Check http://localhost:8000/health returns `{"status": "ok"}`.

**Terminal 4 — Streamlit UI**
```bash
streamlit run app/ui/streamlit_app.py
```
Opens in your browser automatically, usually http://localhost:8501.

## Project structure
```
app/
  main.py                    FastAPI gateway — POST /api/analyze, GET /api/analyze/{job_id}
  api/schemas.py              request/response models
  workers/celery_app.py       Celery config (Redis broker + backend)
  workers/tasks.py            Celery task that calls the model
  models/phishing_model.py    the model itself — swap point, single function contract
  ui/streamlit_app.py         Streamlit frontend, talks to FastAPI only
tests/
  test_model.py               standalone validation of the DistilBERT candidate
  compare_models.py           side-by-side comparison of both candidate models
```

## Current model
`ElSlay/BERT-Phishing-Email-Model` — binary phishing/legitimate classifier.
Swapped in after comparing against `cybersectony/phishing-email-detection-distilbert_v2.4.1`
using `tests/compare_models.py`.

## Notes
- The Celery worker loads the model once at startup, not per-request.
- Model output contract (don't break this if you swap models again):
  `{"prediction": str, "confidence": float, "all_probabilities": dict}`
