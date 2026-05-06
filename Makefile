.PHONY: format lint docstrings format-check typecheck metrics test check ci clean-dist build check-dist publish-test publish

format:
	uv run ruff format src/ scripts/

format-check:
	uv run ruff format --check src/ scripts/

lint:
	uv run ruff check src/ scripts/

docstrings:
	uv run ruff check src/ --select D --ignore D100,D104

typecheck:
	uv run mypy src/

metrics:
	uv run python scripts/code_metrics.py

test:
	@mkdir -p work
	uv run pytest; \
	code=$$?; [ $$code -eq 5 ] && exit 0 || exit $$code

# Local dev: format (mutating) + all checks
check: format lint docstrings typecheck metrics test

# CI: all checks via the consolidated script (no early exit, full summary)
ci:
	@bash scripts/ci.sh

clean-dist:
	rm -rf dist

build: clean-dist
	uv build

check-dist: build
	uv run --with twine twine check dist/*

publish-test: check-dist
	uv run --with twine twine upload --repository testpypi dist/*

publish: check-dist
	uv run --with twine twine upload dist/*
