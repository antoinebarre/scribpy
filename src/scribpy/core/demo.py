"""Demo project creation service."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from scribpy.model import Diagnostic, LintResult
from scribpy.utils import has_errors

DemoVariant = Literal["valid", "invalid"]

_VALID_DEMO_PAGES: tuple[tuple[str, str], ...] = (
    ("guide/getting-started/overview.md", "Getting Started Overview"),
    ("guide/getting-started/installation.md", "Installation Guide"),
    ("guide/getting-started/quickstart.md", "Quickstart"),
    ("guide/workflows/authoring.md", "Authoring Workflow"),
    ("guide/workflows/review.md", "Review Workflow"),
    ("guide/workflows/release.md", "Release Workflow"),
    ("guide/workflows/troubleshooting.md", "Troubleshooting Workflow"),
    ("concepts/docs-as-code.md", "Docs as Code"),
    ("concepts/functional-chains.md", "Functional Chains"),
    ("concepts/semantic-model.md", "Semantic Model"),
    ("concepts/transforms.md", "Transforms"),
    ("architecture/overview.md", "Architecture Overview"),
    ("architecture/pipeline.md", "Pipeline Architecture"),
    ("architecture/data-model.md", "Data Model"),
    ("architecture/extensions.md", "Extension Architecture"),
    ("reference/cli.md", "CLI Reference"),
    ("reference/configuration.md", "Configuration Reference"),
    ("reference/diagnostics.md", "Diagnostics Reference"),
    ("reference/lint-rules.md", "Lint Rules Reference"),
    ("reference/transforms.md", "Transform Reference"),
    ("reference/builders.md", "Builder Reference"),
    ("tutorials/first-project.md", "First Project Tutorial"),
    ("tutorials/multi-file-book.md", "Multi-file Book Tutorial"),
    ("tutorials/custom-index.md", "Custom Index Tutorial"),
    ("tutorials/build-markdown.md", "Build Markdown Tutorial"),
    ("operations/ci.md", "CI Operations"),
    ("operations/release.md", "Release Operations"),
    ("operations/migration.md", "Migration Operations"),
    ("operations/faq.md", "Operations FAQ"),
    ("appendix/glossary.md", "Glossary"),
    ("appendix/roadmap.md", "Roadmap"),
    ("appendix/changelog.md", "Changelog"),
)


def _valid_demo_config() -> str:
    indexed_files = ("index.md", *(path for path, _ in _VALID_DEMO_PAGES))
    entries = "\n".join(f'  "{path}",' for path in indexed_files)
    return f"""\
[project]
name = "scribpy-demo"

[paths]
source = "doc"

[document]
title = "Scribpy Demo Manual"

[document.toc]
enabled = true
max_level = 3
style = "bullet"

[document.numbering]
enabled = true
max_level = 3
style = "decimal"

[index]
mode = "explicit"
files = [
{entries}
]
"""


def _valid_demo_index() -> str:
    return """\
---
title: Scribpy Demo
author: Demo Author
version: 1
tags:
  - scribpy
  - docs-as-code
---

# Scribpy Demo

Welcome to the Scribpy demo project.

This document exercises the complete project preparation, lint, transform, and
Markdown build chains on a non-trivial documentation tree.

## Start Here

Begin with the [overview](guide/getting-started/overview.md), continue with the
[quickstart](guide/getting-started/quickstart.md), then inspect the
[pipeline architecture](architecture/pipeline.md#processing-stages).

## Explore the Manual

- [Docs as Code](concepts/docs-as-code.md)
- [Functional Chains](concepts/functional-chains.md)
- [CLI Reference](reference/cli.md)
- [First Project Tutorial](tutorials/first-project.md)
- [CI Operations](operations/ci.md)
- [Glossary](appendix/glossary.md)

Visit the [Scribpy project](https://github.com/example/scribpy) for more
information.

## Project Structure

The explicit index spans more than thirty Markdown documents across nested
sections, so ordering and link resolution remain deterministic at realistic
scale.

![Scribpy architecture overview](assets/architecture.png)
"""


def _valid_demo_page(index: int, relative_path: str, title: str) -> str:
    previous_path = "index.md" if index == 0 else _VALID_DEMO_PAGES[index - 1][0]
    next_path = (
        "index.md"
        if index == len(_VALID_DEMO_PAGES) - 1
        else _VALID_DEMO_PAGES[index + 1][0]
    )
    current = Path(relative_path)
    previous_link = _relative_link(current, previous_path)
    next_link = _relative_link(current, next_path)
    index_link = _relative_link(current, "index.md")
    extra = _valid_demo_extra(relative_path)
    return f"""\
---
title: {title}
author: Demo Author
---

# {title}

This page belongs to the complex Scribpy demo manual.

## Overview

Use this page to exercise deterministic indexing, semantic extraction, and
assembled output across nested documentation sections.

## Navigation

Return to the [manual index]({index_link}), visit the [previous page]({previous_link}),
or continue to the [next page]({next_link}).
{extra}"""


def _valid_demo_extra(relative_path: str) -> str:
    if relative_path == "guide/getting-started/overview.md":
        return (
            "\nSee the [installation guide](installation.md) before the quickstart.\n"
        )
    if relative_path == "guide/getting-started/installation.md":
        return "\n![Setup diagram](../../assets/setup.png)\n"
    if relative_path == "architecture/pipeline.md":
        return (
            "\n## Processing Stages\n\n"
            "Configure, scan, parse, lint, transform, assemble, then build.\n"
        )
    if relative_path == "reference/diagnostics.md":
        return (
            "\n## Lint Diagnostics\n\n"
            "- `LINT001`\n"
            "- `LINT002`\n"
            "- `LINT003`\n"
            "- `LINT004`\n"
        )
    return ""


def _relative_link(current: Path, target: str) -> str:
    import posixpath

    current_dir = current.parent.as_posix()
    start = current_dir if current_dir != "." else "."
    return posixpath.relpath(target, start=start)


def _valid_demo_readme() -> str:
    return """\
# Scribpy Demo Project

Generated by:

```bash
scribpy demo create
```

The generated manual contains 33 Markdown documents under `doc/`, arranged in a
nested tree that exercises explicit indexing, link resolution, transforms, and
assembled Markdown builds.

## Phase 2 — Project context

```bash
scribpy index check --root .
```

## Phase 3 — Parse and semantic extraction

```bash
scribpy parse check --root .
```

## Phase 4 — Lint-first user value

```bash
scribpy lint --root .
```

## Phases 5–6 — Markdown build and transforms

```bash
scribpy build markdown --root .
```

The demo `scribpy.toml` configures the assembled document title, generated table
of contents, TOC depth, and section-numbering style:

```toml
[document]
title = "Scribpy Demo Manual"

[document.toc]
enabled = true
max_level = 3
style = "bullet"

[document.numbering]
enabled = true
max_level = 3
style = "decimal"
```

## Next steps

Re-run checks after editing the files under `doc/` and observe how diagnostics,
section numbering, generated table of contents, TOC depth, and link rewrites
change.
"""


_VALID_DEMO_FILES: dict[Path, str] = {
    Path("scribpy.toml"): _valid_demo_config(),
    Path("doc/index.md"): _valid_demo_index(),
    **{
        Path("doc") / relative_path: _valid_demo_page(index, relative_path, title)
        for index, (relative_path, title) in enumerate(_VALID_DEMO_PAGES)
    },
    Path("doc/assets/architecture.png"): "demo asset: architecture\n",
    Path("doc/assets/setup.png"): "demo asset: setup\n",
    Path("README.md"): _valid_demo_readme(),
}

_INVALID_DEMO_FILES: dict[Path, str] = {
    Path("scribpy.toml"): """\
[project]
name = "scribpy-invalid-demo"

[paths]
source = "doc"

[document]
title = "Scribpy Invalid Demo Manual"

[document.toc]
enabled = true
max_level = 3
style = "bullet"

[document.numbering]
enabled = true
max_level = 3
style = "decimal"

[index]
mode = "explicit"
files = [
  "index.md",
  "guide/setup.md",
  "guide/lint-lab.md",
]
""",
    Path("doc/index.md"): """\
---
title: Scribpy Invalid Demo
author: Demo Author
---

# Scribpy Invalid Demo

This project is **intentionally invalid** to demonstrate Scribpy diagnostics.

The index is valid, so `scribpy lint` can run and report content issues from
`guide/lint-lab.md`.

See the [setup guide](guide/setup.md) and the
[lint lab](guide/lint-lab.md#exercise).

![Demo image](assets/demo.png)
""",
    Path("doc/guide/setup.md"): """\
---
title: Setup (unlisted)
---

# Setup

This file is valid and keeps the project navigable while the lint lab contains
intentional defects.

## Links

Back to [index](../index.md).
""",
    Path("doc/guide/lint-lab.md"): """\
---
title: Lint Lab
---

## Exercise

This file intentionally has no H1.

### Jumped Heading

The heading level jumps from H2 to H3 without a top-level heading.

See the [missing page](ghost.md).

![Missing diagram](../assets/missing.png)
""",
    Path("doc/assets/demo.png"): "demo asset: invalid variant\n",
    Path("README.md"): """\
# Scribpy Invalid Demo Project

Generated by:

```bash
scribpy demo create --variant invalid
```

## Phase 2 — Project context

```bash
scribpy index check --root .
```

The project context is valid so later checks can run.

## Phase 3 — Parse and semantic extraction

```bash
scribpy parse check --root .
```

Parsing succeeds so the lint phase receives a complete semantic model.

## Phase 4 — Lint-first user value

```bash
scribpy lint --root .
```

Expected diagnostics from `guide/lint-lab.md`:

- `LINT001`: document without H1
- `LINT002`: invalid heading hierarchy
- `LINT003`: broken internal link
- `LINT004`: missing local asset
""",
}

_DEMO_FILES_BY_VARIANT: dict[DemoVariant, dict[Path, str]] = {
    "valid": _VALID_DEMO_FILES,
    "invalid": _INVALID_DEMO_FILES,
}


def create_demo_project(
    target: Path,
    *,
    force: bool = False,
    variant: DemoVariant = "valid",
) -> LintResult:
    """Create a small external Scribpy tutorial project.

    Args:
        target: Directory where the demo project should be created.
        force: When true, overwrite files managed by the demo template.
        variant: Demo template variant. ``"valid"`` creates a project that
            passes ``scribpy index check``; ``"invalid"`` creates a project
            with intentional index diagnostics for tutorial purposes.

    Returns:
        Lint-style result containing user-facing diagnostics. A successful
        creation returns no diagnostics.
    """
    files = _DEMO_FILES_BY_VARIANT[variant]
    diagnostics = _validate_target(target, files=files, force=force)
    if has_errors(diagnostics):
        return LintResult(diagnostics=diagnostics, failed=True)

    try:
        for relative_path, content in files.items():
            path = target / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    except OSError as error:
        diagnostics = (
            Diagnostic(
                severity="error",
                code="DEMO002",
                message=f"Could not create demo project: {error}",
                path=target,
            ),
        )

    return LintResult(diagnostics=diagnostics, failed=has_errors(diagnostics))


def _validate_target(
    target: Path,
    *,
    files: dict[Path, str],
    force: bool,
) -> tuple[Diagnostic, ...]:
    if target.exists() and not target.is_dir():
        return (
            Diagnostic(
                severity="error",
                code="DEMO001",
                message="Demo target exists and is not a directory.",
                path=target,
                hint="Choose a directory path or remove the existing file.",
            ),
        )

    if force:
        return ()

    existing_files = tuple(
        path for path in _planned_paths(target, files=files) if path.exists()
    )
    return tuple(
        Diagnostic(
            severity="error",
            code="DEMO001",
            message="Demo file already exists.",
            path=path,
            hint=(
                "Choose an empty target directory or pass --force to overwrite "
                "demo files."
            ),
        )
        for path in existing_files
    )


def _planned_paths(target: Path, *, files: dict[Path, str]) -> tuple[Path, ...]:
    return tuple(target / relative_path for relative_path in files)


__all__ = ["DemoVariant", "create_demo_project"]
