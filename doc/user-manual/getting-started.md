# Getting Started

## Requirements

- Python **3.12** or newer
- pip or uv

---

## Installation

```bash
pip install scribpy
```

Verify the installation:

```bash
scribpy --help
```

---

## Your first project in five minutes

### 1 — Create the demo project

```bash
scribpy demo create scribpy-demo
```

This writes a complete, self-contained project into `scribpy-demo/`:

```
scribpy-demo/
├── scribpy.toml          # project configuration
└── doc/
    ├── index.md
    ├── guide/
    │   ├── overview.md
    │   └── advanced.md
    └── assets/
        └── logo.png
```

### 2 — Validate the configuration and index

```bash
scribpy index check --root scribpy-demo
```

Expected output:

```text
✔ Resolve project configuration — done
✔ Discover Markdown sources — done
✔ Build document index — done
```

### 3 — Lint the documentation

```bash
scribpy lint --root scribpy-demo
```

The built-in rules check heading structure, broken internal links, and missing
local assets. A clean project exits with code `0` and no error diagnostics.

### 4 — Build

=== "Single-page HTML"

    ```bash
    scribpy build html --mode single-page --root scribpy-demo
    # → scribpy-demo/build/html/index.html
    ```

=== "MkDocs site"

    ```bash
    scribpy build html --mode site --root scribpy-demo
    # → scribpy-demo/build/site/site/
    ```

=== "Assembled Markdown"

    ```bash
    scribpy build markdown --root scribpy-demo
    # → scribpy-demo/build/markdown/document.md
    ```

---

## Creating your own project

### Minimal `scribpy.toml`

Place this file at the root of your documentation project:

```toml
[project]
name = "My Project"

[paths]
source = "doc"

[index]
mode = "filesystem"
```

Scribpy discovers all `*.md` files under `doc/` in deterministic order.

### Explicit document order

When order matters (e.g. a user manual), switch to `explicit` mode:

```toml
[index]
mode = "explicit"
files = [
    "index.md",
    "installation.md",
    "configuration.md",
    "reference.md",
]
```

### Enable the table of contents and section numbering

```toml
[document]
title = "Engineering Handbook"

[document.toc]
enabled = true
max_level = 3
style = "bullet"

[document.numbering]
enabled = true
max_level = 3
style = "decimal"
```

---

## Python quick start

```python
import scribpy

# 1. Create the demo
scribpy.create_demo("scribpy-demo")

# 2. Validate
index_result = scribpy.check_index("scribpy-demo")
scribpy.print_result(index_result)

# 3. Lint
lint_result = scribpy.lint("scribpy-demo")
scribpy.print_result(lint_result)

# 4. Build
build_result = scribpy.build_html("scribpy-demo", mode="site")
scribpy.print_result(build_result)

# 5. Inspect diagnostics programmatically
if not build_result.success:
    for d in build_result.diagnostics:
        print(f"[{d.severity}] {d.code}: {d.message}")
        if d.hint:
            print(f"  hint: {d.hint}")
```

---

## CI/CD integration

Override the output directory to write artefacts to a workspace path chosen by
the pipeline, without modifying `scribpy.toml`:

```bash
scribpy build html --mode site \
    --root docs \
    --output-dir /workspace/artefacts/site
```

Or from Python:

```python
result = scribpy.build_html(
    "docs",
    mode="site",
    output_dir="/workspace/artefacts/site",
)
```

Relative `output_dir` values are resolved from the project root; absolute paths
are used as-is.

---

## Next steps

- Read the [Configuration](configuration.md) reference to understand every `scribpy.toml` key.
- Read the [Pipelines](pipelines.md) page to understand which stages each command runs.
- Read the [Markdown Guide](markdown-guide.md) for best practices on writing Scribpy-compatible Markdown.
