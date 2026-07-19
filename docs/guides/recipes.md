# Common recipes

## Build only when validation succeeds

```shell
scribpy validate handbook && \
scribpy build handbook work/handbook/document.md
```

In Python, preserve the structured report:

```python
report = scribpy.validate_project("handbook")
if not report.is_valid:
    scribpy.render_validation_report(report)
    raise SystemExit(1)

collection = scribpy.MarkdownCollection.from_tree("handbook")
scribpy.concatenate(collection, Path("work/handbook/document.md"))
```

## Use alphabetical discovery for a draft

Omit `order` while exploring. Supported direct children are traversed
alphabetically. Add explicit order before publication when sequence matters.

```yaml
project:
  title: Draft Handbook
```

Be aware that adding a filename changes alphabetical position.

## Share assets between nested pages

Place shared assets under the root and refer to them relative to each page:

```markdown
<!-- index.md -->
![Logo](assets/logo.svg)

<!-- guide/install.md -->
![Logo](../assets/logo.svg)
```

List `assets/` in root order when using an explicit list to avoid an unlisted
directory warning. It contributes no Markdown page when it contains no
Markdown files.

## Disable numbering but keep a TOC

```yaml
build:
  toc: true
  toc_depth: 2
  heading_numbering:
    enabled: false
```

Omitting `heading_numbering` also disables numbering. An existing block
defaults `enabled` to true, so state `false` when the block is retained for
clarity.

## Use a self-hosted PlantUML Server

```yaml
build:
  plantuml_backend: plantuml_server
  plantuml_server_url: https://plantuml.example.internal/plantuml
```

The URL must be absolute HTTP(S). Scribpy removes a trailing slash before
constructing the PNG endpoint.

## Render Mermaid locally

After installing Mermaid CLI:

```yaml
build:
  mermaid_backend: mermaid_cli
  mermaid_command: mmdc
```

If the executable is not on `PATH`, provide a non-empty executable path. Avoid
wrapping shell syntax in the value: Scribpy invokes a command argument list,
not a shell command line.

## Capture validation output in Python

```python
from io import StringIO

from rich.console import Console

buffer = StringIO()
console = Console(file=buffer, force_terminal=False)
is_valid = scribpy.valid_report("handbook", console=console)
text_report = buffer.getvalue()
```

For machine decisions, prefer `validate_project` and inspect diagnostic fields
rather than parsing rendered text.

## Add a custom diagnostic policy

```python
collection = scribpy.MarkdownCollection.from_tree("handbook")
report = collection.diagnose([TodoRule()])
```

Passing a list replaces the defaults for that call; it does not append
automatically. Include default rules explicitly if both sets are required.
See [Extension API](../python-api/extensions.md) for a complete worked
example of writing `TodoRule`.

## Produce Markdown, HTML, and an MkDocs tree from one build

Combine all three output shapes in one script, since none of them mutate
the project source:

```shell
scribpy build handbook work/handbook/document.md
scribpy html work/handbook/document.md work/handbook/document.html
scribpy mkdocs-export handbook work/handbook/site-source
```

Each command reads the same `handbook/scribpy.yml`. Diagram rendering runs
independently for `build` and `mkdocs-export` — expect two separate network
calls per diagram if both backends are remote services, and expect
generated PNGs to differ in file name between the two outputs since each
output tree keeps its own `assets/generated/` directory.

## Point CI at both validation and build

A minimal GitHub Actions-style step sequence, run with `uv`:

```shell
uv run scribpy validate handbook
uv run scribpy build handbook work/handbook/document.md
uv run scribpy html work/handbook/document.md work/handbook/document.html
```

`validate` exits 1 on the first command if there are blocking findings,
which stops the job before a `build` is attempted — no `&&` chaining is
required when each command is its own CI step, since most CI runners treat
a non-zero exit as a failed step automatically.

## Keep manifests under version control, keep `work/` out of it

Add a `.gitignore` entry for your chosen build root so generated output
never gets committed alongside source:

```text
work/
```

Only `scribpy.yml` files and the Markdown sources they order are meant to
be reviewed and diffed; everything under a build root is reproducible from
them by re-running the relevant command.

