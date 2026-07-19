# Python API reference

This page covers every name in `scribpy.__all__` — the complete end-user
surface of the package. Signatures and behavior are summarized from their
Google-style source docstrings. For workflow-level guidance (what to call
when, and why) read [Using the Python API](../python-api/index.md) and the
[end-to-end demo](../python-api/demo.md) instead; this page favors
completeness over narrative.

!!! note "End-user API vs. extension API"
    Everything on this page is importable directly as `scribpy.<name>`.
    Building a custom diagnostic rule or diagram renderer requires importing
    from `scribpy.core.plantuml`, `scribpy.core.mermaid`, or
    `scribpy.core.diagnostics` instead — see
    [Extension API](../python-api/extensions.md), which is documented
    separately and deliberately not summarized here.

## Workflows

| Interface | Purpose and example |
|---|---|
| `validate_project(root: str | Path) -> ProjectValidationReport` | Validate all stages: `report = scribpy.validate_project("notes")`. |
| `valid_report(root, *, console=None) -> bool` | Validate and render: `ok = scribpy.valid_report("notes")`. |
| `render_validation_report(report, *, console=None) -> None` | Render with Rich: `scribpy.render_validation_report(report)`. |
| `concatenate(collection, output: Path) -> None` | Assemble: `scribpy.concatenate(collection, Path("out.md"))`. |
| `html_export(source, output, toc_depth=3, css=None) -> None` | Export assembled Markdown: `scribpy.html_export(Path("out.md"), Path("out.html"))`. |
| `mkdocs_export(source, output) -> None` | Export page tree: `scribpy.mkdocs_export(Path("notes"), Path("site"))`. |
| `init_skeleton(output_dir, *, title, author="", version="0.1.0") -> None` | Create minimal project: `scribpy.init_skeleton(Path("notes"), title="Notes")`. |
| `parse_outline(path, *, max_depth=4) -> list[OutlineNode]` | Parse heading tree: `nodes = scribpy.parse_outline(Path("outline.md"))`. |
| `init_from_outline(outline_path, output_dir, *, max_depth=4) -> None` | Scaffold: `scribpy.init_from_outline(Path("outline.md"), Path("notes"))`. |
| `logging_context(level="INFO", *, file=None, console=True)` | Temporary logging: `with scribpy.logging_context("DEBUG"): ...`. |

### Validation functions

`validate_project(root)` accepts `str` or `Path` and always returns a
`ProjectValidationReport` for expected project-input failures. Inspect
`is_valid` before continuing. The function is appropriate for services, tests,
and applications because it does not print.

`valid_report(root, *, console=None)` calls the validator, renders with Rich,
and returns the same validity as a boolean. Pass a `rich.console.Console` to
redirect or capture presentation. It is a convenience adapter, not a distinct
validation engine.

`render_validation_report(report, *, console=None)` only presents an existing
report. It does not revalidate the filesystem.

```python
report = scribpy.validate_project(Path("notes"))
errors = report.by_severity(scribpy.DiagnosticSeverity.ERROR)
if errors:
    scribpy.render_validation_report(report)
```

### Initialization functions

`init_skeleton(output_dir, *, title, author="", version="0.1.0")` creates the
directory, root manifest, and initial `index.md`. `title` is mandatory and
keyword-only. Empty author metadata is omitted. Existing root manifest raises
`ScaffoldCollisionError` before replacement.

`parse_outline(path, *, max_depth=4)` reads a headings-only UTF-8 file and
returns a mutable list of `OutlineNode` trees. `max_depth` is inclusive and
must be 1–6. Expected structural failures carry a one-based line number in
`OutlineValidationError`.

`init_from_outline(outline_path, output_dir, *, max_depth=4)` combines parsing
and scaffold writing. A leaf heading becomes a stub Markdown page; a heading
with children becomes a directory with a local manifest.

### Assembly and export functions

`concatenate(collection, output)` returns `None`; success is represented by the
written Markdown and asset files. It creates the output parent. Renderer and
filesystem errors are not converted to reports.

`html_export(source, output, toc_depth=3, css=None)` reads an assembled UTF-8
Markdown file. It strips Scribpy's Markdown TOC block from the body, derives
navigation from headings, converts Markdown to HTML, and inlines built-in CSS
and burger-menu JavaScript. It does not create the output parent.

`mkdocs_export(source, output)` loads a project, preserves individual source
pages, renders diagrams, collects images, derives navigation, and writes a
minimal MkDocs configuration. An existing destination configuration raises
`ScaffoldCollisionError` before export.

### Logging context

`logging_context(level="INFO", *, file=None, console=True)` yields the
configured `logging.Logger`. `level` accepts a standard case-insensitive name
or integer. `file` adds an UTF-8 file handler and `console=False` suppresses
stderr. All handlers added by the context are closed and removed on exit, and
the previous logger level is restored.

## Domain models

| Type | Purpose and example |
|---|---|
| `MarkdownFile(path, content, encoding="utf-8")` | File-backed value: `item = scribpy.MarkdownFile.from_path("page.md")`. Methods include `with_content`, `replace_text`, `to_document`, `write`, `verify`, `has_valid_images`, `has_expected_headings`, and `has_expected_yaml`. |
| `MarkdownDocument(content)` | In-memory Markdown: `doc = scribpy.MarkdownDocument("# Title")`; inspect `doc.image_references`. |
| `MarkdownImageReference(alt_text, target, title=None, line=None, column=None)` | Parsed image value: `ref = scribpy.MarkdownImageReference("Logo", "logo.png")`. |
| `MarkdownCollection(root, files, manifest=RootManifest())` | Ordered project: `collection = scribpy.MarkdownCollection.from_tree("notes")`; call `concatenate()` or `diagnose()`. |
| `RootManifest(path=None, project={}, build=..., order=())` | Root configuration: `manifest = scribpy.RootManifest(project={"title": "Notes"})`. |
| `FolderManifest(path=None, title=None, order=())` | Folder configuration: `manifest = scribpy.FolderManifest(title="Guide")`. |
| `OutlineNode(title, level, line_number, children=...)` | Parsed outline node: `root = scribpy.parse_outline(Path("outline.md"))[0]`. |

### `MarkdownFile`

Construction fields are `path: Path`, `content: str`, and `encoding: str =
"utf-8"`. The value is a frozen, slotted dataclass.

| Member | Signature / behavior |
|---|---|
| `from_path` | `from_path(path, *, encoding="utf-8") -> MarkdownFile`; may raise `OSError` or `UnicodeDecodeError`. |
| `name` | Filename including suffix. |
| `suffix` | Final suffix including leading dot. |
| `with_content` | Return a new value with replacement content. |
| `replace_text` | Return a new value after ordinary string replacement. |
| `to_document` | Create a path-free `MarkdownDocument` and extract images. |
| `write` | `write(path=None) -> Path`; create parents and write with stored encoding. |
| `verify` | Run MkForge with optional settings and custom rules. |
| `has_valid_images` | Ask MkForge to validate image references with configurable timeout. |
| `has_expected_headings` | Compare heading pairs, optionally requiring an exact sequence. |
| `has_expected_yaml` | Compare front-matter values, optionally requiring exact keys. |

### `MarkdownDocument` and image references

`MarkdownDocument(content)` extracts `image_references` during construction.
References inside fenced code are ignored. Each
`MarkdownImageReference` records alt text, raw target, optional title, and
optional one-based line/column.

```python
document = scribpy.MarkdownDocument(
    '# Page\n\n![Logo](assets/logo.png "Brand")\n'
)
reference = document.image_references[0]
assert reference.target == "assets/logo.png"
assert reference.title == "Brand"
```

### `MarkdownCollection`

`MarkdownCollection(root, files, manifest=RootManifest())` is normally created
with `from_tree(root, *, encoding="utf-8")`. The factory requires a directory,
loads the root manifest, resolves recursive local order, and reads each page.

`collection.concatenate() -> MarkdownDocument` performs structural
concatenation and heading shifting in memory. It is distinct from public
`scribpy.concatenate(collection, output)`, which applies the remaining
pipeline and writes files.

`collection.diagnose(rules=None)` uses all defaults when `rules` is `None` and
uses exactly the supplied iterable otherwise.

### Manifest and outline models

`RootManifest` and `FolderManifest` are frozen Pydantic models. Root `build` is
a validated internal `BuildSettings` value even though `BuildSettings` is not
exported from `scribpy.__all__`. Prefer loading manifests through a collection
instead of constructing nested settings from unvalidated dictionaries.

`OutlineNode` is a mutable dataclass because the parser builds its child lists
incrementally. `level` is 1–6 and `line_number` is one-based.

## Diagnostics and reports

| Type | Purpose and example |
|---|---|
| `DiagnosticSeverity` | String enum: `scribpy.DiagnosticSeverity.ERROR`. |
| `CollectionDiagnostic` | Finding: `CollectionDiagnostic("CODE", DiagnosticSeverity.INFO, "message")`. |
| `CollectionDiagnosticReport` | Tuple-backed report: `CollectionDiagnosticReport().has_errors` is false. |
| `CollectionDiagnosticRule` | Structural protocol: `rule: scribpy.CollectionDiagnosticRule = TodoRule()`. |
| `ProjectDiagnostic` | Project finding: `ProjectDiagnostic("CODE", DiagnosticSeverity.WARNING, "message")`. |
| `ProjectValidationReport` | Complete result: inspect `is_valid`, `has_errors`, and `by_severity(...)`. |
| `SourceFirstHeadingH1Rule` | `collection.diagnose([scribpy.SourceFirstHeadingH1Rule()])`. |
| `SourceH1CountRule` | `collection.diagnose([scribpy.SourceH1CountRule()])`. |
| `HeadingLevelOverflowRule` | `collection.diagnose([scribpy.HeadingLevelOverflowRule()])`. |
| `InternalMarkdownLinkRule` | `collection.diagnose([scribpy.InternalMarkdownLinkRule()])`. |
| `LocalImageMissingRule` | `collection.diagnose([scribpy.LocalImageMissingRule()])`. |
| `ExternalImageReferenceRule` | `collection.diagnose([scribpy.ExternalImageReferenceRule()])`. |

### Severity and filtering

`DiagnosticSeverity` is a `StrEnum`, so values serialize as `"error"`,
`"warning"`, and `"info"`. Both report types expose `by_severity(severity)`
and return tuples, preserving finding order.

`CollectionDiagnosticReport.has_errors` and
`ProjectValidationReport.has_errors` are booleans. Project reports additionally
offer `is_valid`, the exact inverse of `has_errors`.

### Project report fields

| Field | Meaning |
|---|---|
| `root` | Normalized project path validated. |
| `diagnostics` | Ordered `ProjectDiagnostic` tuple. |
| `markdown_count` | Number of Markdown sources verified by MkForge. |
| `manifest_count` | Number of reachable manifests inspected. |

`ProjectDiagnostic` adds optional `column`, `category`, and `target` to the
collection finding shape. Paths and line/column values may be absent when a
failure belongs to the whole project rather than a source position.

### Exported default rules

The package root exports six rule implementations for direct application use:
first H1, H1 count, heading overflow, internal Markdown links, missing local
images, and external images. Additional default rule types such as
`LocalAnchorLinkRule` and `ImageOutsideRootRule` are available from
`scribpy.core.diagnostics`, not from `scribpy.__all__`.

## Exceptions and warnings

| Type | Raised for; example |
|---|---|
| `ScribpyError` | Base domain failure: `except scribpy.ScribpyError`. |
| `InvalidMarkdownError(detail)` | Blocking Markdown/collection structure: `raise scribpy.InvalidMarkdownError("bad H1")`. |
| `InvalidScribpyManifestError(path, detail)` | Invalid manifest: `except scribpy.InvalidScribpyManifestError`. |
| `PlantUmlRenderError(detail)` | PlantUML provider failure: `except scribpy.PlantUmlRenderError`. |
| `MermaidRenderError(detail)` | Mermaid provider failure: `except scribpy.MermaidRenderError`. |
| `OutlineValidationError(line_number, detail)` | Invalid outline: `except scribpy.OutlineValidationError`. |
| `ScaffoldCollisionError(path)` | Existing target manifest: `except scribpy.ScaffoldCollisionError`. |
| `ScribpyManifestWarning` | Ignored manifest setting: `warnings.simplefilter("error", scribpy.ScribpyManifestWarning)`. |

All exception classes except `ScribpyManifestWarning` inherit from
`ScribpyError`. The warning inherits from `UserWarning` and is emitted through
Python's warnings system rather than raised.

Catching the common base is often the simplest correct choice for an
application boundary that just needs to report failure without
distinguishing cause:

```python
try:
    collection = scribpy.MarkdownCollection.from_tree("notes")
    scribpy.concatenate(collection, Path("out.md"))
except scribpy.ScribpyError as error:
    print(f"Build failed: {error}")
    raise SystemExit(1) from error
```

Catch specific subclasses instead when the caller can react differently —
for example, retrying a `PlantUmlRenderError` against a different server, or
surfacing `ScaffoldCollisionError` as "did you mean to overwrite?" in a CLI
prompt:

```python
try:
    scribpy.mkdocs_export(Path("notes"), Path("site"))
except scribpy.ScaffoldCollisionError:
    print("site/mkdocs.yml already exists; choose a new output directory")
except (scribpy.PlantUmlRenderError, scribpy.MermaidRenderError) as error:
    print(f"Diagram rendering failed: {error.detail}")
```

Public diagnostic attributes:

| Exception | Attributes |
|---|---|
| `InvalidScribpyManifestError` | `path`, `detail` |
| `InvalidMarkdownError` | `detail` |
| `PlantUmlRenderError` | `detail` |
| `MermaidRenderError` | `detail` |
| `OutlineValidationError` | `line_number`, `detail` |
| `ScaffoldCollisionError` | `path` |

Functions also document standard exceptions such as `OSError`,
`UnicodeDecodeError`, `UnicodeEncodeError`, `NotADirectoryError`, and
`ValueError`. Catch them only where the application can add recovery or useful
context.
