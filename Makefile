.PHONY: build test lint serve

build:
	uv build

test:
	uv run pytest

lint:
	uv run ruff check .

serve:
	uv run uvicorn finance.serving.app:app --host 0.0.0.0 --port 8000
