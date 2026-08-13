---
name: 'Python conventions'
description: 'Style and safety rules for all Python in this project'
applyTo: '**/*.py'
---

# Python conventions

Python 3.11. Format with `black`, lint with `ruff`, line length 100.

Type hints on every function signature, including `-> None`. Pydantic models for
anything crossing an HTTP or queue boundary; never pass bare dicts between
services.

No bare `except:`. Catch the specific exception, log it with the job ID, and
return or raise something the caller can act on. An exception that is caught and
ignored needs a comment saying why.

Use `logging`, never `print`. Get the logger with `logging.getLogger(__name__)`.
Log the job ID, the input length, and a hash of the input. Never log message
bodies, upload contents, or user-supplied filenames.

Read configuration from environment variables through a single settings object in
`app/common/config.py`, with defaults that work under Docker Compose. No
hardcoded hosts, ports, connection strings, model IDs, or paths anywhere else. No
secrets in the repository.

Docstrings on public functions only, one line, saying what it does rather than
restating the signature.

Prefer the standard library. A new dependency needs a reason a reviewer would
accept, and it goes in `requirements.txt` in the same change that imports it.