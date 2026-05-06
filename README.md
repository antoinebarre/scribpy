# Scribpy

> A Python toolkit and document compiler for engineering-grade Docs-as-Code workflows.

---

## Overview

**Scribpy** is a Python package (≥ 3.12) designed to be the foundation of a **Docs-as-Code** approach for Markdown-based documentation.

It provides a structured framework to:

- write documentation as version-controlled Markdown files;
- lint and validate Markdown and documentation structure;
- manipulate Markdown programmatically;
- assemble multiple files into complete documents;
- generate tables of contents and section numbering;
- export documentation to Markdown, HTML, and PDF;
- apply CSS styling to HTML and PDF outputs;
- support reproducible documentation builds in local or CI/CD environments.

---

## Docs-as-Code

Scribpy follows the Docs-as-Code principles:

- documentation is stored as plain text and versioned in Git;
- documentation quality is checked automatically before generation;
- builds are reproducible from sources and configuration;
- generated outputs are artifacts, not manually edited deliverables.

```text
Markdown Sources
    ↓
Configuration (scribpy.toml)
    ↓
Linting & Validation
    ↓
Transformation (TOC, includes, numbering, links)
    ↓
Assembly
    ↓
Build Artifacts
    ├── Markdown
    ├── HTML
    └── PDF
```

---

## Installation

```bash
pip install scribpy
```

Requires **Python ≥ 3.12**.

---

## Quick Start

```python
from scribpy.core import load_markdown, get_headings, build_project

doc = load_markdown("docs/architecture.md")

for heading in get_headings(doc):
    print(heading.level, heading.title)

result = build_project(".")
```

---

## CLI

```bash
scribpy init                    # Initialize a project
scribpy lint                    # Validate documentation quality
scribpy build                   # Build all enabled outputs
scribpy build markdown          # Build assembled Markdown
scribpy build html              # Build HTML
scribpy build pdf               # Build PDF
scribpy format docs/            # Format Markdown files
scribpy rewrite-links docs/     # Rewrite internal links
scribpy toc                     # Generate table of contents
scribpy index show              # Display document index
scribpy index check             # Validate document index
scribpy clean                   # Remove build artifacts
```

---

## Configuration

Scribpy uses a `scribpy.toml` configuration file:

```toml
[project]
name = "System Engineering Handbook"
version = "1.0.0"
authors = ["Engineering Team"]
language = "en"

[paths]
source = "docs"
assets = "assets"
styles = "styles"
output = "build"

[document]
entrypoint = "index.md"
title = "System Engineering Handbook"
number_sections = true
include_toc = true

[lint]
enabled = true
fail_on_warning = false

[builders.html]
enabled = true
css = ["styles/html.css"]

[builders.pdf]
enabled = true
engine = "weasyprint"
css = ["styles/pdf.css"]
```

---

## Package Architecture

```text
src/scribpy/
├── cli/          — Command-line interface
├── core/         — Public Python API facade
├── config/       — scribpy.toml loading and validation
├── project/      — Project scanning and document index
├── model/        — Core data types (frozen dataclasses)
├── parser/       — Markdown parsing layer
├── lint/         — Documentation quality engine
├── transforms/   — Transformation pipeline (TOC, includes, numbering)
├── builders/     — Output generation (Markdown, HTML, PDF)
├── themes/       — Templates and CSS themes
├── assets/       — Images, diagrams, static files
├── extensions/   — Plugin registry
└── utils/        — Low-level path, string, I/O helpers
```

---

## Project Layout

A typical Scribpy documentation project:

```text
my-documentation/
├── scribpy.toml
├── docs/
│   ├── index.md
│   ├── introduction.md
│   └── architecture.md
├── assets/
│   └── images/
├── styles/
│   ├── html.css
│   └── pdf.css
└── build/
    ├── markdown/
    ├── html/
    └── pdf/
```

---

## Development

```bash
uv sync --dev       # install package + dev dependencies
make check          # format · lint · typecheck · test
```

Individual commands:

| Command          | Description                        |
|------------------|------------------------------------|
| `make format`    | Auto-format with ruff              |
| `make lint`      | Lint with ruff                     |
| `make typecheck` | Type-check with mypy (strict mode) |
| `make test`      | Run tests with coverage report     |

---

## Design

Scribpy favors a functional programming style:

- pure functions over mutable objects;
- frozen dataclasses for data containers;
- dependency injection over inheritance;
- protocols for injectable services;
- explicit pipeline stages with typed inputs and outputs.

See [doc/SDD.md](doc/SDD.md) for the full Software Design Document.

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Commit following [Conventional Commits](https://www.conventionalcommits.org/)
4. Open a pull request

Code must comply with SOLID principles, Google Python Style Guide, full type hints,
and cyclomatic complexity < 5 per function.

---

## License

MIT © Antoine
