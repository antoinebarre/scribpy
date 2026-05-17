# Public Classes & Types

All result, data, and configuration classes are **frozen dataclasses** — they
are immutable after construction. Import them directly from `scribpy`:

```python
from scribpy import BuildResult, LintResult, ParseResult, BuildArtifact
```

---

## Result types

### `BuildResult`

Returned by `build_html()` and `build_markdown()`.

```python
@dataclass(frozen=True)
class BuildResult:
    success: bool
    artifacts: tuple[BuildArtifact, ...]
    diagnostics: tuple[Diagnostic, ...]
```

| Field | Type | Description |
|---|---|---|
| `success` | `bool` | `True` when the build completed without blocking errors. |
| `artifacts` | `tuple[BuildArtifact, ...]` | Produced output files. A failed build may still carry partial artifacts. |
| `diagnostics` | `tuple[Diagnostic, ...]` | All diagnostics from preparation, linting, transforms, and writing. |

**Usage example:**

```python
result = scribpy.build_html("my-project", mode="site")

if result.success:
    primary = result.artifacts[0]
    print(f"Site built at: {primary.path}")
else:
    errors = [d for d in result.diagnostics if d.severity == "error"]
    print(f"{len(errors)} error(s) prevented the build")
```

---

### `LintResult`

Returned by `lint()`, `check_index()`, and `create_demo()`.

```python
@dataclass(frozen=True)
class LintResult:
    diagnostics: tuple[Diagnostic, ...]
    failed: bool
```

| Field | Type | Description |
|---|---|---|
| `diagnostics` | `tuple[Diagnostic, ...]` | Validation or lint diagnostics. |
| `failed` | `bool` | `True` when at least one `"error"` severity diagnostic was emitted. |

**Usage example:**

```python
result = scribpy.lint("my-project")

if result.failed:
    for d in result.diagnostics:
        if d.severity == "error":
            print(f"  [{d.code}] {d.message}")
```

---

### `ParseResult`

Returned by `check_parse()`.

```python
@dataclass(frozen=True)
class ParseResult:
    documents: tuple[Document, ...]
    diagnostics: tuple[Diagnostic, ...]
    failed: bool
```

| Field | Type | Description |
|---|---|---|
| `documents` | `tuple[Document, ...]` | Successfully parsed documents in index order. |
| `diagnostics` | `tuple[Diagnostic, ...]` | Reading, parsing, and extraction diagnostics. |
| `failed` | `bool` | `True` when parsing encountered a blocking error. |

**Usage example:**

```python
result = scribpy.check_parse("my-project")

for doc in result.documents:
    print(f"{doc.relative_path}")
    for h in doc.headings:
        print(f"  {'#' * h.level} {h.title}")
```

---

### `BuildArtifact`

One produced output file or directory.

```python
@dataclass(frozen=True)
class BuildArtifact:
    path: Path
    target: str
    artifact_type: str
    metadata: Mapping[str, object] | None = None
```

| Field | Type | Description |
|---|---|---|
| `path` | `Path` | Absolute path to the produced file or directory. |
| `target` | `str` | Target family: `"markdown"`, `"html"`, `"html-site"`, or `"assets"`. |
| `artifact_type` | `str` | Specific kind: `"document"`, `"page"`, `"site"`, `"stylesheet"`, or `"image"`. |
| `metadata` | `Mapping[str, object] \| None` | Optional informational metadata (MkDocs config path, etc.). |

---

## `Diagnostic`

A single diagnostic message produced at any pipeline stage.

```python
@dataclass(frozen=True)
class Diagnostic:
    severity: Literal["info", "warning", "error"]
    code: str
    message: str
    path: Path | None = None
    line: int | None = None
    hint: str | None = None
```

| Field | Type | Description |
|---|---|---|
| `severity` | `"info"` / `"warning"` / `"error"` | Severity level. `"error"` blocks the build; others do not. |
| `code` | `str` | Stable identifier, e.g. `LINT001`. Use this for filtering in automation. |
| `message` | `str` | Human-readable explanation. |
| `path` | `Path \| None` | Related source file path, if applicable. |
| `line` | `int \| None` | One-based source line number, if applicable. |
| `hint` | `str \| None` | Remediation guidance. |

**Usage example:**

```python
result = scribpy.lint("my-project")

for d in result.diagnostics:
    location = ""
    if d.path:
        location = f" ({d.path}:{d.line or '?'})"
    print(f"[{d.severity.upper()}] {d.code}{location}: {d.message}")
    if d.hint:
        print(f"  → {d.hint}")
```

---

## Document model

Parsed document objects are accessible via `ParseResult.documents`.

### `Document`

```python
@dataclass(frozen=True)
class Document:
    path: Path
    relative_path: Path
    source: str
    frontmatter: Mapping[str, Any]
    ast: MarkdownAst
    title: str | None
    headings: tuple[Heading, ...]
    links: tuple[Reference, ...]
    assets: tuple[AssetRef, ...]
```

| Field | Type | Description |
|---|---|---|
| `path` | `Path` | Absolute path to the source file. |
| `relative_path` | `Path` | Path relative to `paths.source`. |
| `source` | `str` | Raw Markdown source (frontmatter stripped). |
| `frontmatter` | `Mapping[str, Any]` | Parsed YAML/TOML frontmatter. |
| `ast` | `MarkdownAst` | Internal AST representation. |
| `title` | `str \| None` | First `# H1` text found, if any. |
| `headings` | `tuple[Heading, ...]` | All headings extracted from the document. |
| `links` | `tuple[Reference, ...]` | All links and cross-references. |
| `assets` | `tuple[AssetRef, ...]` | All asset references (images, diagrams, etc.). |

### `Heading`

```python
@dataclass(frozen=True)
class Heading:
    level: int
    title: str
    anchor: str | None = None
    line: int | None = None
```

### `Reference`

```python
@dataclass(frozen=True)
class Reference:
    kind: Literal["link", "image", "xref"]
    target: str
    text: str | None = None
    path: Path | None = None
    line: int | None = None
```

### `AssetRef`

```python
@dataclass(frozen=True)
class AssetRef:
    kind: Literal["image", "diagram", "static"]
    target: str
    path: Path | None = None
    title: str | None = None
    line: int | None = None
```

---

## Configuration classes

These classes model the contents of `scribpy.toml`. They are produced by the
config loader and available on the internal `Config` object (accessible via
`scribpy.core` for advanced use).

| Class | Description |
|---|---|
| `Config` | Root configuration object holding all sections. |
| `ProjectConfig` | `[project]` — project name. |
| `PathConfig` | `[paths]` — `source` directory. |
| `IndexConfig` | `[index]` — discovery mode and explicit file list. |
| `DocumentConfig` | `[document]` — title, TOC, and numbering settings. |
| `TocConfig` | `[document.toc]` — table-of-contents settings. |
| `NumberingConfig` | `[document.numbering]` — section-numbering settings. |
| `HtmlBuilderConfig` | `[builders.html]` — HTML mode, CSS, site name, theme, output dir. |

### `HtmlBuilderConfig`

```python
@dataclass(frozen=True)
class HtmlBuilderConfig:
    mode: Literal["single-page", "site"] = "single-page"
    css_files: tuple[Path, ...] = ()
    site_name: str | None = None
    theme: str | None = None
    output_dir: Path | None = None
```

#### `HtmlBuilderConfig.resolve_output_dir() -> Path`

Returns the configured `output_dir` when set, otherwise the mode-appropriate
default:

- `"single-page"` → `build/html`
- `"site"` → `build/site`

---

## Service protocols

For advanced use with dependency injection (e.g. in tests or custom pipelines),
Scribpy defines these protocols under `scribpy.model`:

| Protocol | Description |
|---|---|
| `FileSystem` | Abstraction over file I/O (`read_text`, `write_text`, `exists`, `glob`). |
| `MarkdownParser` | Abstraction over Markdown parsing (`parse(source) -> MarkdownAst`). |
| `HtmlRenderer` | Abstraction over HTML rendering. |
| `PdfRenderer` | Abstraction over PDF rendering (future). |

Pass custom implementations to core functions via the `filesystem=` or
`parser=` keyword arguments to substitute real I/O in tests.
