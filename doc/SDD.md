# Software Design Document — Scribpy

> Documentation should be engineered like software.

**Version:** 0.2.0-draft
**Date:** 2026-05-06
**Author:** Antoine Barré

---

## 1. Purpose

This document describes the software design of **Scribpy**, a Python toolkit and document compiler for engineering-grade Docs-as-Code workflows.

It covers:

- the project's goals and positioning;
- the overall architecture and processing pipeline;
- the responsibilities of each package;
- the core data types;
- the design patterns applied;
- the error handling contract;
- the SOLID principles as applied in this project.

---

## 2. Docs-as-Code Positioning

Scribpy follows the Docs-as-Code paradigm:

- documentation is authored as plain Markdown;
- sources are versioned in Git;
- quality is checked automatically before builds;
- outputs are reproducible artifacts, not manually edited deliverables;
- the Markdown source repository is the authoritative source of truth.

Processing flow:

```text
Markdown Sources
    ↓
Configuration (scribpy.toml)
    ↓
Linting & Validation
    ↓
Transformation (TOC, includes, numbering, links)
    ↓
Assembly
    ↓
Build Artifacts
    ├── Markdown
    ├── HTML
    └── PDF
```

---

## 3. Package Architecture

```text
src/scribpy/
├── cli/          — Command-line interface
├── core/         — Public Python API facade
├── config/       — Configuration loading and validation
├── project/      — Project scanning and document index
├── model/        — Core data types (frozen dataclasses)
├── parser/       — Markdown parsing layer
├── lint/         — Documentation quality engine
├── transforms/   — Document transformation pipeline
├── builders/     — Output generation (Markdown, HTML, PDF)
├── themes/       — Templates and CSS themes
├── assets/       — Images, diagrams, static files
├── extensions/   — Plugin registry
└── utils/        — Low-level helpers
```

---

## 4. Package Responsibilities

### 4.1 `scribpy.cli`

Exposes command-line commands. Contains no business logic.
Delegates all processing to application services.

Commands:

| Command                     | Description                          |
|-----------------------------|--------------------------------------|
| `scribpy init`              | Initialize a project                 |
| `scribpy lint`              | Run documentation quality checks     |
| `scribpy build`             | Build all enabled output formats     |
| `scribpy build markdown`    | Build assembled Markdown             |
| `scribpy build html`        | Build HTML output                    |
| `scribpy build pdf`         | Build PDF output                     |
| `scribpy format <path>`     | Format Markdown files with ruff      |
| `scribpy rewrite-links`     | Rewrite internal links               |
| `scribpy toc`               | Generate or update table of contents |
| `scribpy index show`        | Display document index               |
| `scribpy index check`       | Validate document index              |
| `scribpy index generate`    | Generate index from filesystem       |
| `scribpy index add <file>`  | Add a file to the index              |
| `scribpy clean`             | Remove build artifacts               |

### 4.2 `scribpy.core`

Public Python API facade. The stable user-facing interface.

```python
from scribpy.core import (
    load_markdown,
    save_markdown,
    get_headings,
    get_links,
    replace_link,
    normalize_markdown,
    merge_documents,
    split_document,
    generate_toc,
    lint_project,
    build_project,
)
```

Internal packages are free to evolve; only `core` is stable.

### 4.3 `scribpy.config`

Reads and validates `scribpy.toml`.

Main functions:

```python
find_config(start: Path) -> Path | None
load_toml_config(path: Path) -> dict[str, Any]
parse_config(raw: Mapping[str, Any]) -> Config
validate_config(config: Config) -> list[Diagnostic]
load_config(path: Path) -> tuple[Config | None, list[Diagnostic]]
```

Key principle: separate parsing from validation. User mistakes return
`Diagnostic` objects; unexpected failures raise exceptions.

### 4.4 `scribpy.project`

Builds the project view from configuration and filesystem.
Filesystem access is injected via the `FileSystem` protocol.

Main functions:

```python
scan_project(root, config, fs) -> tuple[SourceFile, ...]
build_document_index(config, files) -> tuple[DocumentIndex, list[Diagnostic]]
validate_document_index(index, files) -> list[Diagnostic]
load_project(root, services) -> tuple[Project | None, list[Diagnostic]]
```

Index modes:

| Mode         | Description                                               |
|--------------|-----------------------------------------------------------|
| `explicit`   | Order fully controlled by `scribpy.toml` (recommended)   |
| `filesystem` | Files sorted by discovery order                           |
| `hybrid`     | Auto-discovery with optional overrides                    |

### 4.5 `scribpy.model`

Frozen dataclasses that flow through the pipeline:

| Type            | Description                                  |
|-----------------|----------------------------------------------|
| `Project`       | Top-level project state                      |
| `SourceFile`    | A file discovered in the project             |
| `Document`      | A parsed Markdown document                   |
| `MarkdownAst`   | Parser output (tokens + backend tag)         |
| `Heading`       | A heading node                               |
| `Reference`     | A link or cross-reference                    |
| `AssetRef`      | An image, diagram, or static asset reference |
| `DocumentIndex` | Ordered index of files for assembly          |
| `Diagnostic`    | An error, warning, or info message           |

### 4.6 `scribpy.parser`

Converts Markdown source into normalized document structures.
The parser implementation is injected via the `MarkdownParser` protocol.

```python
class MarkdownParser(Protocol):
    def parse(self, source: str) -> MarkdownAst: ...
```

Main functions:

```python
parse_markdown(source, parser) -> MarkdownAst
parse_frontmatter(source) -> tuple[dict[str, Any], str]
parse_document_file(source_file, reader, parser) -> Document
parse_documents(files, services) -> tuple[Document, ...]
extract_headings(ast) -> tuple[Heading, ...]
extract_links(ast) -> tuple[Reference, ...]
extract_assets(ast) -> tuple[AssetRef, ...]
```

### 4.7 `scribpy.lint`

Documentation quality engine. A lint rule is a plain callable:

```python
LintRule = Callable[[LintContext], Sequence[Diagnostic]]
```

Built-in checks:

| Rule code  | Check                                         | Default severity |
|------------|-----------------------------------------------|------------------|
| `LINT001`  | Missing H1 heading                            | error            |
| `LINT002`  | Heading hierarchy violation (level skipped)   | error            |
| `LINT003`  | Broken internal link                          | error            |
| `LINT004`  | Broken image reference                        | error            |
| `LINT005`  | Duplicate anchor                              | warning          |
| `LINT006`  | Missing frontmatter                           | warning          |
| `LINT007`  | Trailing whitespace                           | warning          |

Main functions:

```python
run_lint_rules(context, rules) -> list[Diagnostic]
select_lint_rules(config, registry) -> tuple[LintRule, ...]
lint_project(project, documents, registry) -> LintResult
should_fail_build(diagnostics, config) -> bool
```

### 4.8 `scribpy.transforms`

Document transformation engine. A transform is a plain callable:

```python
Transform = Callable[[TransformContext], TransformResult]
```

Built-in transforms (applied in order):

1. `resolve_includes` — expand include directives
2. `resolve_cross_references` — resolve internal references
3. `apply_section_numbering` — prefix headings with section numbers
4. `render_diagrams` — render Mermaid / PlantUML blocks
5. `rewrite_links_for_target` — adapt links for the output format
6. `generate_toc_transform` — inject table of contents

Transforms return new document collections; they never mutate in place.

### 4.9 `scribpy.builders`

Output generation. A builder is a plain callable:

```python
Builder = Callable[[BuildContext], BuildResult]
```

| Target     | Description                                   |
|------------|-----------------------------------------------|
| `markdown` | Assembled single-file Markdown                |
| `html`     | Single-page or multi-page HTML via template   |
| `pdf`      | PDF via WeasyPrint or Pandoc                  |

Rendering engines (`HtmlRenderer`, `PdfRenderer`) are injected.

### 4.10 `scribpy.themes`

Manages HTML and PDF rendering templates and CSS stylesheets.

```python
load_theme(name, theme_paths) -> Theme
resolve_css_files(config, target) -> tuple[Path, ...]
render_template(template, context) -> str
```

### 4.11 `scribpy.assets`

Manages images, diagrams, and static files referenced by Markdown.

```python
collect_assets(documents) -> tuple[AssetRef, ...]
validate_assets(project, assets) -> list[Diagnostic]
copy_assets(assets, output_dir, fs) -> tuple[BuildArtifact, ...]
render_mermaid(source, renderer) -> RenderedAsset
render_plantuml(source, renderer) -> RenderedAsset
```

External rendering tools (Mermaid CLI, PlantUML) are isolated behind
the `DiagramRenderer` protocol.

### 4.12 `scribpy.extensions`

Plugin registry. Registry updates return new instances (immutable).

```python
create_default_registry() -> ExtensionRegistry
register_lint_rule(registry, name, rule) -> ExtensionRegistry
register_transform(registry, name, transform) -> ExtensionRegistry
register_builder(registry, name, builder) -> ExtensionRegistry
load_extensions(config, registry) -> tuple[ExtensionRegistry, list[Diagnostic]]
```

### 4.13 `scribpy.utils`

Low-level, reusable helpers with no dependency on high-level Scribpy objects.

Planned sub-modules:

| Sub-module          | Responsibilities                                  |
|---------------------|---------------------------------------------------|
| `utils.file_utils`  | Markdown file discovery and I/O (implemented)     |
| `utils.markdown_generator` | Random GFM document generator (implemented) |
| `utils.paths`       | Path normalization, `ensure_relative_to`          |
| `utils.strings`     | `slugify`, text normalization                     |
| `utils.toml`        | TOML reading helpers                              |
| `utils.yaml`        | YAML reading helpers                              |
| `utils.hashing`     | Deterministic content hashes for cache keys       |
| `utils.io`          | Generic `read_text` / `write_text`                |
| `utils.diagnostics` | Diagnostic formatting and aggregation             |
| `utils.collections` | `unique_preserve_order` and similar               |

---

## 5. Core Data Types

### `Config`

```python
@dataclass(frozen=True)
class Config:
    project: ProjectConfig
    paths: PathConfig
    document: DocumentConfig
    markdown: MarkdownConfig
    lint: LintConfig
    index: IndexConfig
    transforms: TransformConfig
    builders: BuilderConfig
    assets: AssetConfig
    extensions: ExtensionConfig
```

Location: `scribpy/config/types.py`

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

Location: `scribpy/model/document.py`

### `Diagnostic`

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

Location: `scribpy/model/diagnostic.py`

Full type contracts for all model types are defined in `scribpy/model/`.

---

## 6. Application Services

```python
@dataclass(frozen=True)
class AppServices:
    fs: FileSystem
    parser: MarkdownParser
    html_renderer: HtmlRenderer
    pdf_renderer: PdfRenderer
    registry: ExtensionRegistry
    logger: Logger
```

Protocols:

```python
class FileSystem(Protocol):
    def read_text(self, path: Path) -> str: ...
    def write_text(self, path: Path, content: str) -> None: ...
    def exists(self, path: Path) -> bool: ...
    def glob(self, root: Path, pattern: str) -> Iterable[Path]: ...

class HtmlRenderer(Protocol):
    def render(self, document: AssembledDocument, css_files: Sequence[Path]) -> str: ...

class PdfRenderer(Protocol):
    def render(self, html: str, css_files: Sequence[Path], output_path: Path) -> None: ...
```

Main application functions:

```python
run_lint(root, services) -> LintResult
run_build(root, targets, services) -> BuildResult
run_format(root, services) -> FormatResult
run_index_check(root, services) -> LintResult
```

---

## 7. Design Patterns

### Pipeline Pattern

The main processing chain is a sequential pipeline:

```text
scan → parse → lint → transform → assemble → build
```

Each step receives explicit inputs and returns explicit outputs.

### Strategy Pattern

Used for interchangeable behaviors:

- Markdown parser implementation (`MarkdownParser` protocol)
- PDF rendering engine (`PdfRenderer` protocol)
- HTML rendering mode (`HtmlRenderer` protocol)
- Lint rule execution (`LintRule` callable)
- Asset processing (`DiagramRenderer` protocol)
- Output builders (`Builder` callable)

### Registry Pattern

Used to register named callables:

- lint rules → `ExtensionRegistry.lint_rules`
- transforms → `ExtensionRegistry.transforms`
- builders → `ExtensionRegistry.builders`
- renderers → `ExtensionRegistry.renderers`

### Adapter Pattern

Used to integrate external tools:

- `markdown-it-py` — Markdown parser adapter
- `WeasyPrint` — PDF renderer adapter
- `Pandoc` — alternative PDF/HTML renderer adapter
- `Mermaid CLI` — diagram renderer adapter
- `PlantUML` — diagram renderer adapter

### Facade Pattern

`scribpy.core` exposes a simple user-facing API that hides pipeline complexity.

### Command Pattern

Each CLI command maps to a callable application service.

### Dependency Injection

Services (filesystem, parser, renderer, registry, logger) are injected
rather than hard-coded. This enables unit testing and implementation swapping.

---

## 8. Error Handling Contract

### User-facing diagnostics

For expected documentation or configuration problems, return `Diagnostic` objects:

- broken link;
- missing file;
- invalid heading hierarchy;
- invalid configuration value.

### Internal exceptions

For unexpected programming errors or unrecoverable technical failures, raise exceptions:

```python
class ScribpyError(Exception): ...
class ConfigLoadError(ScribpyError): ...
class BuildExecutionError(ScribpyError): ...
```

General rule:

```text
User mistake → Diagnostic
Programming or infrastructure failure → Exception
```

---

## 9. SOLID Principles

| Principle                   | Application in Scribpy                                                           |
|-----------------------------|----------------------------------------------------------------------------------|
| Single Responsibility       | Each function does one thing: parse config, scan files, parse Markdown, …        |
| Open / Closed               | Registries and callables allow extension without modifying core logic            |
| Liskov Substitution         | Protocols (`MarkdownParser`, `FileSystem`, …) allow safe substitution            |
| Interface Segregation       | Small protocols are preferred over large service interfaces                      |
| Dependency Inversion        | High-level orchestration depends on protocols, not concrete implementations      |

---

## 10. Configuration File Reference

Default configuration file: `scribpy.toml`

Key sections:

| Section              | Responsibility                                          |
|----------------------|---------------------------------------------------------|
| `[project]`          | Project metadata (name, version, authors, language)     |
| `[paths]`            | Source, assets, styles, templates, output directories   |
| `[document]`         | Entrypoint, title, TOC, section numbering               |
| `[markdown]`         | Markdown flavor and extensions                          |
| `[lint]`             | Lint rules and severity                                 |
| `[index]`            | Document index mode and ordered file list               |
| `[transforms]`       | Enabled transformation steps                            |
| `[builders.markdown]`| Assembled Markdown output settings                      |
| `[builders.html]`    | HTML output settings and CSS                            |
| `[builders.pdf]`     | PDF output settings and CSS                             |
| `[assets]`           | Asset copying and validation                            |
| `[extensions]`       | Plugin list                                             |

---

## 11. Build Artifacts

```text
build/
├── markdown/
│   └── document.md
├── html/
│   └── index.html
└── pdf/
    └── document.pdf
```

Generated files must not be manually edited.
The Markdown source repository is the authoritative source of truth.

---

## 12. Typical Project Layout

```text
my-documentation/
├── scribpy.toml
├── docs/
│   ├── index.md
│   ├── introduction.md
│   ├── architecture.md
│   └── requirements.md
├── assets/
│   ├── images/
│   └── diagrams/
├── styles/
│   ├── html.css
│   └── pdf.css
├── templates/
│   ├── html/
│   └── pdf/
└── build/
    ├── markdown/
    ├── html/
    └── pdf/
```
