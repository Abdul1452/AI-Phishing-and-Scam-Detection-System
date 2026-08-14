.PHONY: up down test lint fmt logs

up:
	docker compose up --build

down:
	docker compose down -v

test:
	CELERY_TASK_ALWAYS_EAGER=1 python -m pytest

lint:
	ruff check . && black --check .

fmt:
	ruff check --fix . && black .

logs:
	docker compose logs -f worker
