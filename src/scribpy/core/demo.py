"""Demo project creation service."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from scribpy.core.demo_assets import DEMO_CSS
from scribpy.logging import get_logger, prepare_logging
from scribpy.model import Diagnostic, LintResult
from scribpy.utils import has_errors

DemoVariant = Literal["valid", "invalid"]
logger = get_logger(__name__)

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
    """Return valid demo config."""
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

[builders.html]
mode = "single-page"
css_files = ["theme/demo.css"]
theme = "readthedocs"

[index]
mode = "explicit"
files = [
{entries}
]
"""


def _valid_demo_index() -> str:
    """Return valid demo index."""
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

![Scribpy architecture overview](assets/architecture.svg)
"""


def _valid_demo_page(index: int, relative_path: str, title: str) -> str:
    """Return valid demo page."""
    extra = _valid_demo_extra(relative_path)
    return f"""\
---
title: {title}
author: Demo Author
---

# {title}

This section belongs to the complex Scribpy demo manual.

## Overview

Use this section to exercise deterministic indexing, semantic extraction, and
assembled output across nested documentation sections.

## In the assembled manual

When Scribpy builds the final document, this source file is merged into one
continuous publication according to the explicit index order. The result is a
single manual with deterministic section numbering, generated table of
contents, and resolved cross-references.
{extra}"""


def _valid_demo_extra(relative_path: str) -> str:
    """Return valid demo extra."""
    if relative_path == "guide/getting-started/overview.md":
        return (
            "\nSee the [installation guide](installation.md) before the quickstart.\n"
        )
    if relative_path == "guide/getting-started/installation.md":
        return "\n![Setup diagram](../../assets/setup.svg)\n"
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


def _valid_demo_readme() -> str:
    """Return valid demo readme."""
    return """\
# Scribpy Demo Project

Generated by:

```bash
scribpy demo create
```

The generated manual contains 33 Markdown documents under `doc/`, arranged in a
nested tree that exercises explicit indexing, link resolution, transforms,
assembled Markdown builds, single-page HTML output, and MkDocs-backed site
generation.

## End-to-end walkthrough

Run the commands below from this demo directory, in order. They mirror the
normal Scribpy workflow: validate the project, inspect semantics, lint content,
then build the publication targets.

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

This writes:

```text
build/markdown/document.md
```

## Phase 7 — HTML outputs

Build the portable single-page document:

```bash
scribpy build html --mode single-page --root .
```

Inspect:

```text
build/html/index.html
build/html/css/demo.css
build/html/assets/
```

Then build the multi-page documentation site:

```bash
scribpy build html --mode site --root .
```

Scribpy prepares the MkDocs inputs and wraps `mkdocs build` itself. Inspect:

```text
build/site/mkdocs.yml
build/site/docs/
build/site/site/index.html
```

Use `single-page` when you need one distributable document. Use `site` when you
need a browsable multi-page documentation website.

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

[builders.html]
mode = "single-page"
css_files = ["theme/demo.css"]
theme = "readthedocs"
```

## Next steps

1. Edit one or two files under `doc/`.
2. Re-run the quality gates:

   ```bash
   scribpy index check --root .
   scribpy parse check --root .
   scribpy lint --root .
   ```

3. Rebuild the publication targets:

   ```bash
   scribpy build markdown --root .
   scribpy build html --mode single-page --root .
   scribpy build html --mode site --root .
   ```

4. Compare `build/markdown/document.md`, `build/html/index.html`, and
   `build/site/site/index.html` to see how the same corpus is published in each
   format.

The configured site theme is `readthedocs`; change `builders.html.theme` to try
another MkDocs theme.

## Execution logs

Enable execution logs when you want to inspect the chain without changing the
diagnostics policy:

```bash
scribpy --log-level INFO build html --mode site --root .
```

By default, the log file is written to:

```text
build/logs/scribpy.log
```

Use a custom path or mirror logs to the console when needed:

```bash
scribpy --log-level DEBUG --log-console --log-file logs/demo.log lint --root .
```

The Python API exposes the same capability:

```python
import scribpy

with scribpy.logging_context(level="INFO"):
    scribpy.build_html(".", mode="site")
```
"""


_VALID_DEMO_FILES: dict[Path, str] = {
    Path("scribpy.toml"): _valid_demo_config(),
    Path("doc/index.md"): _valid_demo_index(),
    **{
        Path("doc") / relative_path: _valid_demo_page(index, relative_path, title)
        for index, (relative_path, title) in enumerate(_VALID_DEMO_PAGES)
    },
    Path("doc/assets/architecture.svg"): """\
<svg xmlns="http://www.w3.org/2000/svg" width="960" height="360"
     viewBox="0 0 960 360" role="img" aria-labelledby="title desc">
  <title id="title">Scribpy architecture overview</title>
  <desc id="desc">
    Source Markdown flows through parse, lint, transform, and build stages.
  </desc>
  <rect width="960" height="360" rx="24" fill="#f8fafc"/>
  <g font-family="system-ui, sans-serif" font-size="24" text-anchor="middle">
    <rect x="40" y="120" width="170" height="110" rx="16"
          fill="#dbeafe" stroke="#2563eb"/>
    <text x="125" y="170" fill="#1e3a8a">Markdown</text>
    <text x="125" y="202" fill="#1e3a8a">sources</text>
    <rect x="250" y="120" width="170" height="110" rx="16"
          fill="#dcfce7" stroke="#16a34a"/>
    <text x="335" y="186" fill="#166534">Parse</text>
    <rect x="460" y="120" width="170" height="110" rx="16"
          fill="#fef3c7" stroke="#d97706"/>
    <text x="545" y="186" fill="#92400e">Lint</text>
    <rect x="670" y="120" width="120" height="110" rx="16"
          fill="#ede9fe" stroke="#7c3aed"/>
    <text x="730" y="186" fill="#5b21b6">Build</text>
    <rect x="830" y="120" width="90" height="110" rx="16"
          fill="#fee2e2" stroke="#dc2626"/>
    <text x="875" y="172" fill="#991b1b">HTML</text>
    <text x="875" y="204" fill="#991b1b">Site</text>
  </g>
  <g stroke="#475569" stroke-width="5" stroke-linecap="round">
    <path d="M210 175h30"/>
    <path d="M420 175h30"/>
    <path d="M630 175h30"/>
    <path d="M790 175h30"/>
  </g>
</svg>
""",
    Path("doc/assets/setup.svg"): """\
<svg xmlns="http://www.w3.org/2000/svg" width="840" height="300"
     viewBox="0 0 840 300" role="img" aria-labelledby="title desc">
  <title id="title">Setup flow</title>
  <desc id="desc">Install Scribpy, create a demo, run checks, then build outputs.</desc>
  <rect width="840" height="300" rx="24" fill="#fff7ed"/>
  <g font-family="system-ui, sans-serif" font-size="22" text-anchor="middle">
    <circle cx="100" cy="150" r="62" fill="#ffedd5" stroke="#ea580c"/>
    <text x="100" y="145" fill="#9a3412">Install</text>
    <text x="100" y="174" fill="#9a3412">Scribpy</text>
    <circle cx="300" cy="150" r="62" fill="#dbeafe" stroke="#2563eb"/>
    <text x="300" y="145" fill="#1e3a8a">Create</text>
    <text x="300" y="174" fill="#1e3a8a">demo</text>
    <circle cx="500" cy="150" r="62" fill="#dcfce7" stroke="#16a34a"/>
    <text x="500" y="145" fill="#166534">Run</text>
    <text x="500" y="174" fill="#166534">checks</text>
    <circle cx="700" cy="150" r="62" fill="#ede9fe" stroke="#7c3aed"/>
    <text x="700" y="145" fill="#5b21b6">Build</text>
    <text x="700" y="174" fill="#5b21b6">outputs</text>
  </g>
  <g stroke="#9a3412" stroke-width="5" stroke-linecap="round">
    <path d="M162 150h76"/>
    <path d="M362 150h76"/>
    <path d="M562 150h76"/>
  </g>
</svg>
""",
    Path("theme/demo.css"): DEMO_CSS,
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
    if variant not in _DEMO_FILES_BY_VARIANT:
        return LintResult(
            diagnostics=(
                Diagnostic(
                    severity="error",
                    code="DEMO003",
                    message=f"Unsupported demo variant: {variant}",
                    hint="Use variant='valid' or variant='invalid'.",
                ),
            ),
            failed=True,
        )
    files = _DEMO_FILES_BY_VARIANT[variant]
    prepare_logging(target)
    logger.info("Creating %s demo project at %s", variant, target)
    diagnostics = _validate_target(target, files=files, force=force)
    if has_errors(diagnostics):
        logger.error("Demo creation failed with %d diagnostic(s)", len(diagnostics))
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

    result = LintResult(diagnostics=diagnostics, failed=has_errors(diagnostics))
    logger.info("Created demo project with %d managed file(s)", len(files))
    return result


def _validate_target(
    target: Path,
    *,
    files: dict[Path, str],
    force: bool,
) -> tuple[Diagnostic, ...]:
    """Validate target."""
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
    """Return planned paths."""
    return tuple(target / relative_path for relative_path in files)


__all__ = ["DemoVariant", "create_demo_project"]
