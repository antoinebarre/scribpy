# CLAUDE.md

## Project

`scribpy` is a Python package (>= 3.12) that publishes Markdown files to HTML
or PDF. Two features:

1. **Single page** — one `.md` file to one `.html` or `.pdf`.
2. **Multi-page site** — a collection of `.md` files to an HTML site (via
   MkDocs) or a consolidated PDF.

Diagrams (Mermaid, PlantUML) embedded in Markdown are supported.

Related packages (not dependencies):
- **mkforge** (PyPI) — programmatic Markdown report generation & validation.
- **yggtools** (PyPI) — dev quality pipeline (lint, format, test, metrics).

## Development

```bash
uv sync --group dev    # install deps
make check             # run all quality checks via yggtools
make test              # run tests only
make format            # auto-format code
make ci                # full pipeline with artifacts
```

## Code Standards

- SOLID principles strictly applied
- Functional programming preferred; dataclasses for data
- Design patterns: Strategy, Adapter, Pipeline, Registry — only when justified
- Dependency injection over inheritance
- Google Python Style Guide
- Full type hints on all public functions and methods
- Cyclomatic complexity < 5 per function
- Conventional Commits (`feat:`, `fix:`, `refactor:`, etc.)
