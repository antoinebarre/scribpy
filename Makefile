.PHONY: format lint format-check typecheck test check ci clean-dist build check-dist publish-test publish

format:
	uv run ruff format src/ tests/

format-check:
	uv run ruff format --check src/ tests/

lint:
	uv run ruff check src/ tests/

typecheck:
	uv run mypy src/

test:
	@mkdir -p work
	uv run pytest; \
	code=$$?; [ $$code -eq 5 ] && exit 0 || exit $$code

# Local dev: format (mutating) + all checks
check: format lint typecheck test

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
