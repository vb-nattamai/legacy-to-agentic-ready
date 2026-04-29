.PHONY: install test run lint

install:
	pip install -e ".[dev]" 2>/dev/null || pip install -r requirements.txt

test:
	pytest

run:
	python app.py

lint:
	ruff check .
	ruff format --check .
