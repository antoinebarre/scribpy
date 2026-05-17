# Python API reference

The top-level package is the supported user-facing Python API:

```python
import scribpy
```

## `create_demo`

```python
scribpy.create_demo(
    target: str | Path = "scribpy-demo",
    *,
    force: bool = False,
    variant: Literal["valid", "invalid"] = "valid",
) -> LintResult
```

Create a tutorial project. `variant="valid"` creates a passing project;
`variant="invalid"` creates a project with intentional lint failures.

## `check_index`

```python
scribpy.check_index(root: str | Path | None = None) -> LintResult
```

Run project discovery and index validation only. Use this when you want a fast
configuration/layout check before parsing Markdown content.

## `check_parse`

```python
scribpy.check_parse(root: str | Path | None = None) -> ParseResult
```

Run the shared preparation pipeline through Markdown parsing and return parsed
`Document` objects plus diagnostics.

## `lint`

```python
scribpy.lint(root: str | Path | None = None) -> LintResult
```

Run built-in lint rules over parsed documents. Expected user-input problems are
reported as diagnostics instead of exceptions.

## `build_markdown`

```python
scribpy.build_markdown(
    root: str | Path | None = None,
    *,
    output_dir: str | Path | None = None,
) -> BuildResult
```

Build one assembled Markdown document. Relative `output_dir` values are
project-relative; absolute values are preserved.

## `build_html`

```python
scribpy.build_html(
    root: str | Path | None = None,
    *,
    mode: Literal["single-page", "site"] = "single-page",
    output_dir: str | Path | None = None,
) -> BuildResult
```

Build HTML output. `mode="single-page"` returns one self-contained document;
`mode="site"` writes a MkDocs scaffold and rendered static site.

## `print_result`

```python
scribpy.print_result(result, *, file: TextIO | None = None) -> None
```

Render a compact human-readable summary of a `BuildResult`, `LintResult`, or
`ParseResult`. Detailed diagnostic data remains available on the result object.

## `logging_context`

```python
with scribpy.logging_context(
    level="INFO",
    console=False,
    file=True,
    file_path=None,
):
    ...
```

Enable bounded execution logging for a Python workflow. Relative `file_path`
values are resolved from the detected project root.

## Error model

Expected project/content failures are represented as diagnostics on result
objects. Exceptions remain relevant for programmer errors, invalid custom
extensions, or unexpected runtime failures.
