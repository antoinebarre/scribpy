# Development Checks — Scribpy

**Version:** 0.1.0-draft  
**Date:** 2026-05-06  
**Scope:** local and CI quality controls

---

## 1. Purpose

This document explains the quality checks used during Scribpy development:
formatting, linting, docstring validation, typing, tests, coverage, and
distribution checks.

The goal is to make `make check` understandable and reproducible. Each check
must have a clear purpose, a stable command, and an explicit configuration
source.

---

## 2. Command Overview

Main local command:

```text
make check
```

Execution order:

```text
format -> lint -> docstrings -> typecheck -> test
```

Defined in `Makefile`:

| Target | Command | Purpose |
|--------|---------|---------|
| `format` | `uv run ruff format src/ tests/` | Apply automatic formatting |
| `lint` | `uv run ruff check src/ tests/` | Run static lint rules |
| `docstrings` | `uv run ruff check src/ --select D --ignore D100,D104` | Check Google-style source docstrings |
| `typecheck` | `uv run mypy src/` | Run strict static typing |
| `test` | `uv run pytest` | Run tests and coverage |
| `check` | `format lint docstrings typecheck test` | Run the full local quality gate |

`make check` is intentionally mutating because `format` rewrites files. For a
non-mutating formatting check, use:

```text
make format-check
```

---

## 3. Formatting

Command:

```text
uv run ruff format src/ tests/
```

Configuration:

```toml
[tool.ruff]
cache-dir = "work/.ruff_cache"
```

Controlled points:

- Python source formatting under `src/`;
- test formatting under `tests/`;
- deterministic formatting through Ruff's formatter.

Rationale:

- formatting is automated instead of debated in review;
- generated cache stays under `work/`, not in the user home or repository root.

---

## 4. Static Lint

Command:

```text
uv run ruff check src/ tests/
```

Configuration:

```toml
[tool.ruff.lint]
select = ["E", "F", "I", "UP"]
```

Controlled rule families:

| Code family | Meaning |
|-------------|---------|
| `E` | pycodestyle errors |
| `F` | Pyflakes correctness checks |
| `I` | import sorting |
| `UP` | pyupgrade modernization |

Controlled points:

- syntax-level and import correctness;
- unused imports and undefined names;
- import ordering;
- modern Python syntax for the supported Python version.

Rationale:

- this is a compact baseline with low noise;
- it catches common correctness issues without forcing broad style rules too
  early.

---

## 5. Docstring Rules

Command:

```text
uv run ruff check src/ --select D --ignore D100,D104
```

Configuration:

```toml
[tool.ruff.lint.pydocstyle]
convention = "google"
```

Controlled points:

- public functions and classes in `src/` have docstrings where required;
- docstrings follow the Google convention recognized by Ruff/pydocstyle;
- sections such as `Args`, `Returns`, `Raises`, and `Attributes` follow the
  expected structure;
- docstring formatting issues such as missing summary separation or invalid
  escape sequences are reported.

Ignored rules:

| Rule | Reason |
|------|--------|
| `D100` | Module docstrings are useful but not mandatory for every source module yet |
| `D104` | Package `__init__.py` files are export façades and are not forced to carry package-level documentation |

Scope:

- `src/` only.
- `tests/` are excluded from docstring checks to avoid requiring docstrings on
  every test function and test class.

Rationale:

- source APIs must be documented consistently;
- tests should stay readable without boilerplate;
- `__init__.py` files are excluded from coverage and should remain lightweight
  export façades, not containers for business logic.

---

## 6. Type Checking

Command:

```text
uv run mypy src/
```

Configuration:

```toml
[tool.mypy]
strict = true
packages = ["scribpy"]
cache_dir = "work/.mypy_cache"
```

Controlled points:

- strict typing for source code;
- typed package importability;
- no implicit optional misuse;
- no untyped definitions where mypy strict requires annotations;
- mypy cache stored under `work/`.

Rationale:

- Scribpy's architecture relies on typed contracts and immutable data objects;
- type errors should be caught before functional chains are built on top of
  unstable interfaces.

---

## 7. Tests and Coverage

Command:

```text
uv run pytest
```

Configuration:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--tb=short --cov=src/scribpy --cov-report=term-missing --cov-report=xml:work/coverage.xml --cov-report=html:work/htmlcov --junitxml=work/junit.xml"
pythonpath = ["src"]
cache_dir = "work/.pytest_cache"
```

Coverage configuration:

```toml
[tool.coverage.run]
data_file = "work/.coverage"
source = ["src/scribpy"]
omit = [
    "src/scribpy/__init__.py",
    "src/scribpy/__main__.py",
    "src/scribpy/**/__init__.py",
]

[tool.coverage.report]
fail_under = 80
show_missing = true
```

Controlled points:

- all tests under `tests/`;
- source coverage under `src/scribpy`;
- short tracebacks for readable failure output;
- terminal missing-line coverage report;
- XML report for CI tooling;
- HTML report for local inspection;
- JUnit report for CI test result ingestion.

Generated files:

| Path | Purpose |
|------|---------|
| `work/.coverage` | Coverage data file |
| `work/coverage.xml` | Coverage XML report |
| `work/htmlcov/` | HTML coverage report |
| `work/junit.xml` | JUnit test report |
| `work/.pytest_cache` | Pytest cache |

Coverage omissions:

- `src/scribpy/__init__.py`;
- `src/scribpy/__main__.py`;
- all package `__init__.py` files.

Rationale:

- `__init__.py` files should stay as import/export façades;
- business logic must live in regular modules so it is covered;
- excluding `__init__.py` avoids false pressure to test import plumbing while
  preserving coverage pressure on real logic.

Important rule:

```text
Do not put business logic in __init__.py.
```

If logic appears in `__init__.py`, it may be excluded from coverage and create a
false sense of test safety.

---

## 8. CI Command

Command:

```text
make ci
```

Implementation:

```text
bash scripts/ci.sh
```

Purpose:

- run the consolidated CI workflow;
- allow CI to report a full summary instead of stopping at the first local
  `make check` failure.

`make check` remains the local fast feedback command.

---

## 9. Distribution Checks

Commands:

```text
make build
make check-dist
```

Defined behavior:

| Target | Command | Purpose |
|--------|---------|---------|
| `clean-dist` | `rm -rf dist` | Remove previous distribution artifacts |
| `build` | `uv build` | Build package distributions |
| `check-dist` | `uv run --with twine twine check dist/*` | Validate built distributions |

Rationale:

- distribution validation is separate from `make check`;
- local development checks stay fast;
- packaging checks are available before publishing.

---

## 10. Current Quality Gate

The current local gate is:

```text
make check
```

It controls:

1. formatting;
2. static lint;
3. Google-style source docstrings;
4. strict typing;
5. tests;
6. coverage threshold and reports.

Expected successful output includes:

```text
ruff format: unchanged or reformatted
ruff check: All checks passed
docstrings: All checks passed
mypy: Success
pytest: all tests passed
coverage: fail_under reached
```

---

## 11. Documentation Layout

Development decision records live under:

```text
doc/adr/
```

This separates ADRs from package-level design documentation such as:

- `doc/SDD.md`;
- `doc/FUNCTIONAL_CHAINS.md`;
- this check policy document.

ADRs are development governance documents. They describe decisions, rationale,
and trade-offs; they are not user-facing package documentation.
