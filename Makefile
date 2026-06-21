.PHONY: clean format check ci test build clean-dist check-dist publish-test publish

clean:
	@mkdir -p work
	@find work -mindepth 1 -maxdepth 1 ! -name .gitignore -exec rm -rf {} + || \
		( sleep 0.2 && find work -mindepth 1 -maxdepth 1 ! -name .gitignore -exec rm -rf {} + )

format:
	uv run ruff format src/ tests/

check: clean
	uv run yggtools run --all

ci: clean
	uv run yggtools pipeline

test:
	@mkdir -p work
	uv run pytest; \
	code=$$?; [ $$code -eq 5 ] && exit 0 || exit $$code

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
