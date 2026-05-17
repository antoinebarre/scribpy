# Public classes

## Result classes

### `BuildResult`

| Field | Type | Meaning |
| --- | --- | --- |
| `success` | `bool` | Whether the build completed successfully. |
| `artifacts` | `tuple[BuildArtifact, ...]` | Produced artifacts. Failed builds may still expose partial artifacts. |
| `diagnostics` | `tuple[Diagnostic, ...]` | Diagnostics emitted during preparation, linting, transforms, or writing. |

### `LintResult`

| Field | Type | Meaning |
| --- | --- | --- |
| `diagnostics` | `tuple[Diagnostic, ...]` | Validation or lint diagnostics. |
| `failed` | `bool` | Whether at least one blocking error was found. |

### `ParseResult`

| Field | Type | Meaning |
| --- | --- | --- |
| `documents` | `tuple[Document, ...]` | Parsed documents successfully produced. |
| `diagnostics` | `tuple[Diagnostic, ...]` | Reading, parsing, and extraction diagnostics. |
| `failed` | `bool` | Whether parsing should be treated as failed. |

### `BuildArtifact`

| Field | Type | Meaning |
| --- | --- | --- |
| `path` | `Path` | Produced file or directory path. |
| `target` | `str` | Target family such as `markdown`, `html`, `html-site`, or `assets`. |
| `artifact_type` | `str` | Specific kind such as `document`, `page`, `site`, `stylesheet`, or `image`. |
| `metadata` | `Mapping[str, object] | None` | Optional informational metadata. |

## Diagnostics

### `Diagnostic`

| Field | Meaning |
| --- | --- |
| `severity` | `info`, `warning`, or `error`. |
| `code` | Stable diagnostic identifier such as `LINT001`. |
| `message` | Human-readable explanation. |
| `path` | Optional related file path. |
| `line` | Optional one-based source line. |
| `hint` | Optional remediation guidance. |

## Configuration classes

The following typed classes model `scribpy.toml`:

| Class | Purpose |
| --- | --- |
| `Config` | Full parsed configuration. |
| `ProjectConfig` | Project metadata. |
| `PathConfig` | Filesystem paths, currently `source`. |
| `IndexConfig` | Index mode and explicit file list. |
| `DocumentConfig` | Document title plus TOC/numbering settings. |
| `TocConfig` | Generated table-of-contents settings. |
| `NumberingConfig` | Generated section-numbering settings. |
| `HtmlBuilderConfig` | HTML mode, CSS, site name, theme, output directory. |

### `HtmlBuilderConfig.resolve_output_dir()`

Returns the explicit `output_dir` when configured, otherwise:

- `build/html` for `single-page`;
- `build/site` for `site`.
