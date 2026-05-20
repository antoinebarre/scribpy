# Python API

The top-level `scribpy` package exposes the workflows most users need.

| Function | Purpose |
| --- | --- |
| `create_demo()` | Create a tutorial project. |
| `check_index()` | Validate configuration, discovery, and index consistency. |
| `check_parse()` | Parse indexed Markdown documents. |
| `lint()` | Run documentation lint rules. |
| `build_markdown()` | Build one assembled Markdown document. |
| `build_html()` | Build single-page HTML or a MkDocs-backed site. |
| `print_result()` | Render concise human-readable console output. |

## Demo and validation

```python
import scribpy

scribpy.create_demo("demo")
scribpy.print_result(scribpy.check_index("demo"))
scribpy.print_result(scribpy.check_parse("demo"))
scribpy.print_result(scribpy.lint("demo"))
```

## Build outputs

```python
import scribpy

markdown = scribpy.build_markdown("demo", output_dir="build/ci-markdown")
single_page = scribpy.build_html("demo", mode="single-page")
site = scribpy.build_html("demo", mode="site", output_dir="/tmp/site-artifacts")
```

### Parameter choices

- `build_html(mode=...)` accepts `"single-page"` or `"site"`.
- `create_demo(variant=...)` accepts `"valid"` or `"invalid"`.
- `output_dir` accepts `str` or `Path`; relative values are project-relative,
  absolute values are preserved.
- `root` accepts a project root, a child path, a direct `scribpy.toml` path, or
  `None` to use the current working directory.

## Results and failures

Scribpy returns typed result objects instead of raising for expected user input
problems:

```python
result = scribpy.build_html("demo", mode="site")
if not result.success:
    for diagnostic in result.diagnostics:
        print(diagnostic.code, diagnostic.message)
```

Use `result.success` for build workflows and `result.failed` for parse/lint
workflows. Diagnostics carry `severity`, `code`, `message`, optional `path`,
optional `line`, and optional `hint`.

## Logging

```python
with scribpy.logging_context(level="INFO", console=True):
    scribpy.build_html("demo", mode="site")
```

By default, file logs are written to `build/logs/scribpy.log` below the resolved
project root. Set `file_path=` to choose another file.
