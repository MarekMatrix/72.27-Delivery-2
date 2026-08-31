.PHONY: install test run lint clean

install:
	uv sync

test:
	uv run pytest tests/ -v

run:
	uv run python -m ga_triangles.cli --help

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache
