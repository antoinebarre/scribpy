# scribpy

> Manipulate, edit, and generate documents from Markdown files.

## Overview

`scribpy` is a Python package that treats Markdown as a first-class source of truth for document workflows. It lets you parse, transform, and export `.md` files into structured output formats (PDF, HTML, …) with a clean, composable API.

## Features

- **Parse** — Convert Markdown into an abstract document model
- **Edit** — Programmatically manipulate headings, sections, metadata, and content blocks
- **Generate** — Export to multiple output formats from a single source
- **Extend** — Plugin-friendly pipeline for custom transformations

## Installation

```bash
pip install scribpy
```

Requires **Python ≥ 3.13**.

## Quick Start

```python
from scribpy import Document

doc = Document.from_file("report.md")

doc.replace_section("Summary", "Updated summary content.")

doc.export("report.pdf")
doc.export("report.docx")
```

## Project Structure

```
scribpy/
├── core/          # Document model & AST
├── parsers/       # Markdown ingestion
├── editors/       # Mutation helpers
├── exporters/     # Output format adapters
└── plugins/       # Extension points
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Commit your changes following [Conventional Commits](https://www.conventionalcommits.org/)
4. Open a pull request

Code must comply with SOLID principles, Google Python Style Guide, full type hints, and cyclomatic complexity < 5 per function.

## License

MIT © Antoine