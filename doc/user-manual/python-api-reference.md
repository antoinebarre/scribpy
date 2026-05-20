# Python API Reference

The top-level `scribpy` package is the sole supported user-facing Python API.
All public names are importable directly from it:

```python
import scribpy

# or selectively:
from scribpy import build_html, lint, print_result, LintResult, BuildResult
```

**Public exports:**

```python
__all__ = [
    "BuildArtifact",
    "BuildResult",
    "LintResult",
    "ParseResult",
    "__version__",
    "build_html",
    "build_markdown",
    "check_index",
    "check_parse",
    "create_demo",
    "lint",
    "logging_context",
    "print_result",
]
```

---

## `create_demo`

```python
scribpy.create_demo(
    target: str | Path = "scribpy-demo",
    *,
    force: bool = False,
    variant: Literal["valid", "invalid"] = "valid",
) -> LintResult
```

Create a self-contained tutorial project at `target`.

**Parameters:**

| Name | Type | Default | Description |
|---|---|---|---|
| `target` | `str \| Path` | `"scribpy-demo"` | Destination directory (created if absent). |
| `force` | `bool` | `False` | Overwrite demo-managed files if they already exist. |
| `variant` | `"valid"` / `"invalid"` | `"valid"` | `"valid"` creates a passing project; `"invalid"` creates a project with intentional lint failures. |

**Returns:** `LintResult` — diagnostics from the demo project's initial lint run.

**Examples:**

```python
import scribpy

# Create the default valid demo
result = scribpy.create_demo("my-demo")
scribpy.print_result(result)

# Create an invalid demo to explore error diagnostics
result = scribpy.create_demo("bad-demo", variant="invalid")
for d in result.diagnostics:
    print(f"[{d.severity}] {d.code}: {d.message}")

# Recreate a demo (overwrite existing files)
scribpy.create_demo("my-demo", force=True)
```

---

## `check_index`

```python
scribpy.check_index(root: str | Path | None = None) -> LintResult
```

Validate project discovery and index configuration without parsing Markdown
content. This is the fastest pipeline operation — it runs only configuration
loading, source discovery, and index validation.

**Parameters:**

| Name | Type | Default | Description |
|---|---|---|---|
| `root` | `str \| Path \| None` | `None` | Project root, a child path, or a direct path to `scribpy.toml`. `None` uses the current working directory. |

**Returns:** `LintResult` with `failed=True` if any blocking error is found.

**Examples:**

```python
import scribpy

result = scribpy.check_index("my-project")
scribpy.print_result(result)

if result.failed:
    raise SystemExit("Project index is invalid")
```

---

## `check_parse`

```python
scribpy.check_parse(root: str | Path | None = None) -> ParseResult
```

Run the full preparation pipeline through Markdown parsing and return the
parsed `Document` objects plus any diagnostics.

**Parameters:**

| Name | Type | Default | Description |
|---|---|---|---|
| `root` | `str \| Path \| None` | `None` | Project root, child path, or `scribpy.toml` path. |

**Returns:** `ParseResult` — parsed documents, diagnostics, and `failed` flag.

**Examples:**

```python
import scribpy

result = scribpy.check_parse("my-project")
print(f"Parsed {len(result.documents)} documents")

for doc in result.documents:
    print(f"  {doc.relative_path}: {len(doc.headings)} headings")
```

---

## `lint`

```python
scribpy.lint(root: str | Path | None = None) -> LintResult
```

Run all active lint rules over the parsed documents and return the collected
diagnostics.

**Parameters:**

| Name | Type | Default | Description |
|---|---|---|---|
| `root` | `str \| Path \| None` | `None` | Project root, child path, or `scribpy.toml` path. |

**Returns:** `LintResult` — diagnostics from all lint rules, `failed=True` if
any error diagnostic was emitted.

**Examples:**

```python
import scribpy
import sys

result = scribpy.lint("my-project")
scribpy.print_result(result)

if result.failed:
    sys.exit(1)

# Inspect diagnostics by severity
errors = [d for d in result.diagnostics if d.severity == "error"]
warnings = [d for d in result.diagnostics if d.severity == "warning"]
print(f"{len(errors)} errors, {len(warnings)} warnings")
```

---

## `build_markdown`

```python
scribpy.build_markdown(
    root: str | Path | None = None,
    *,
    output_dir: str | Path | None = None,
) -> BuildResult
```

Build one assembled Markdown document from all indexed source files.
The full pipeline runs: preparation → lint → transforms → merge → write.

**Parameters:**

| Name | Type | Default | Description |
|---|---|---|---|
| `root` | `str \| Path \| None` | `None` | Project root, child path, or `scribpy.toml` path. |
| `output_dir` | `str \| Path \| None` | `None` | Output directory for `document.md`. Relative paths are project-relative. `None` uses `build/markdown`. |

**Returns:** `BuildResult` — `success`, produced `artifacts`, and `diagnostics`.

**Examples:**

```python
import scribpy

# Default output at build/markdown/document.md
result = scribpy.build_markdown("my-project")
scribpy.print_result(result)

# Custom output directory
result = scribpy.build_markdown("my-project", output_dir="/tmp/ci/markdown")

if result.success:
    for artifact in result.artifacts:
        print(f"Produced: {artifact.path}")
```

---

## `build_html`

```python
scribpy.build_html(
    root: str | Path | None = None,
    *,
    mode: Literal["single-page", "site"] = "single-page",
    output_dir: str | Path | None = None,
    extra_css: list[str | Path] | None = None,
) -> BuildResult
```

Build HTML output. Choose between a single self-contained HTML file or a full
MkDocs-backed static site.

**Parameters:**

| Name | Type | Default | Description |
|---|---|---|---|
| `root` | `str \| Path \| None` | `None` | Project root, child path, or `scribpy.toml` path. |
| `mode` | `"single-page"` / `"site"` | `"single-page"` | Output mode. |
| `output_dir` | `str \| Path \| None` | `None` | Override the configured output directory for this run. |
| `extra_css` | `list[str \| Path] \| None` | `None` | Additional CSS files to embed or copy. Paths relative to the project root. |

**Default output directories:**

| Mode | Default |
|---|---|
| `single-page` | `build/html/index.html` |
| `site` | `build/site/site/` |

**Returns:** `BuildResult` — `success`, produced `artifacts`, and `diagnostics`.

**Examples:**

```python
import scribpy

# Single-page HTML
result = scribpy.build_html("my-project")
scribpy.print_result(result)

# MkDocs site
result = scribpy.build_html("my-project", mode="site")

# Custom output dir (useful in CI)
result = scribpy.build_html(
    "my-project",
    mode="site",
    output_dir="/workspace/artefacts/site",
)

# Single-page with additional CSS
result = scribpy.build_html(
    "my-project",
    extra_css=["theme/custom.css"],
)

if not result.success:
    for d in result.diagnostics:
        if d.severity == "error":
            print(f"  {d.code}: {d.message}")
            if d.hint:
                print(f"  → {d.hint}")
```

---

## `print_result`

```python
scribpy.print_result(
    result: BuildResult | LintResult | ParseResult,
    *,
    file: TextIO | None = None,
) -> None
```

Render a compact, human-readable summary of any result object to stdout (or
the given `file`). On success the output is minimal; on failure the diagnostics
are expanded with code, location, message, and hint.

**Parameters:**

| Name | Type | Default | Description |
|---|---|---|---|
| `result` | `BuildResult \| LintResult \| ParseResult` | required | The result to render. |
| `file` | `TextIO \| None` | `None` | Output stream. Defaults to `sys.stdout`. |

**Examples:**

```python
import scribpy
import sys

result = scribpy.lint("my-project")

# Print to stdout
scribpy.print_result(result)

# Print to stderr
scribpy.print_result(result, file=sys.stderr)

# Capture output
import io
buf = io.StringIO()
scribpy.print_result(result, file=buf)
output = buf.getvalue()
```

---

## `logging_context`

```python
from contextlib import contextmanager

scribpy.logging_context(
    *,
    level: str | int = "INFO",
    console: bool = False,
    file: bool = True,
    file_path: str | Path | None = None,
) -> Iterator[None]
```

Context manager that enables bounded execution logging for a Python workflow.
Logging is disabled outside the context. Multiple nested contexts are supported.

**Parameters:**

| Name | Type | Default | Description |
|---|---|---|---|
| `level` | `str \| int` | `"INFO"` | Log level (`"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`, or integer). |
| `console` | `bool` | `False` | Also stream log output to stderr. |
| `file` | `bool` | `True` | Write logs to a file. |
| `file_path` | `str \| Path \| None` | `None` | Custom log file path. Relative paths are resolved from the project root. `None` uses `build/logs/scribpy.log`. |

**Examples:**

```python
import scribpy

# Basic logging to file
with scribpy.logging_context(level="INFO"):
    result = scribpy.build_html("my-project", mode="site")

# DEBUG logging to console and file
with scribpy.logging_context(level="DEBUG", console=True):
    result = scribpy.lint("my-project")

# Custom log file path
with scribpy.logging_context(
    level="WARNING",
    file_path="/var/log/docs-build.log",
):
    result = scribpy.build_markdown("my-project")
```

---

## Error model

Scribpy distinguishes two kinds of failure:

**Diagnostic failures** — expected user-content problems (malformed Markdown,
broken links, missing files). These are represented as `Diagnostic` objects
on result types and never raise exceptions. Use `result.failed` / `result.success`
to detect them.

**Exceptions** — programmer errors, invalid custom extensions, or unexpected
runtime failures. These propagate as regular Python exceptions and are not
caught by Scribpy.

```python
import scribpy

result = scribpy.build_html("my-project", mode="site")

# Check for diagnostic failures
if not result.success:
    for d in result.diagnostics:
        print(f"[{d.severity}] {d.code}: {d.message}")
        if d.path:
            print(f"  file: {d.path}:{d.line or '?'}")
        if d.hint:
            print(f"  hint: {d.hint}")
```
