# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`scribpy` is a Python package (≥ 3.12) that parses, transforms, and exports Markdown files into structured output formats (PDF, HTML, DOCX, …). The public API centres on a `Document` class that can load a `.md` file, mutate its content programmatically, and export it to multiple targets.

## Development Setup

```bash
pip install -e .
python main.py        # prints placeholder "Hello from scribpy!"
```

No test or lint tooling is configured yet. When adding them, prefer `ruff` for linting/formatting and `pytest` for tests.

## Planned Architecture

```
scribpy/
├── core/          # Document model & AST
├── parsers/       # Markdown ingestion
├── editors/       # Mutation helpers
├── exporters/     # Output format adapters
└── plugins/       # Extension points
```

The intended flow is: **parser** reads `.md` → **core** builds an AST/document model → **editors** mutate it in place → **exporters** render it to a target format. **plugins** can hook into any stage of the pipeline.

## Code Standards

From the README, all code must follow:

- **SOLID principles**
- Prefere functional programming instead of Object Oriented except for data (use dataclass)
- boost the maintenability of the code : use classical design pattern
- injection instead of inheritances
- **Google Python Style Guide**
- **Full type hints** on all public functions and methods
- **Cyclomatic complexity < 5** per function
- **Conventional Commits** for commit messages (`feat:`, `fix:`, `refactor:`, etc.)