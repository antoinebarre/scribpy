.PHONY: format lint typecheck test check

format:
	uv run ruff format src/ tests/

lint:
	uv run ruff check src/ tests/

typecheck:
	uv run mypy src/

test:
	uv run pytest --cov=scribpy --cov-report=term-missing; \
	code=$$?; [ $$code -eq 5 ] && exit 0 || exit $$code

check: format lint typecheck test
