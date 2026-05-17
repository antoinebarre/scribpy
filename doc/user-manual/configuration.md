# Configuration

Scribpy is configured through a `scribpy.toml` file placed at the project root.
Scribpy walks up the directory tree from the path passed to `--root` (or the
current working directory) until it finds this file.

---

## Minimal configuration

```toml
[project]
name = "My Project"

[paths]
source = "doc"

[index]
mode = "filesystem"
```

All other keys have sensible defaults and are optional.

---

## Full reference

### `[project]`

Project-level metadata.

| Key | Type | Default | Description |
|---|---|---|---|
| `name` | `string` | `null` | Human-readable project name used in HTML output titles. |

```toml
[project]
name = "Engineering Handbook"
```

---

### `[paths]`

Filesystem paths relative to the project root.

| Key | Type | Default | Description |
|---|---|---|---|
| `source` | `string` | `"doc"` | Directory containing Markdown source files. |

```toml
[paths]
source = "docs"
```

!!! warning "Path must stay inside the project"
    Scribpy validates that `paths.source` does not escape the project root
    (e.g. via `../`). A diagnostic is emitted and the build is aborted if it does.

---

### `[index]`

Controls how Scribpy discovers and orders documents.

| Key | Type | Default | Description |
|---|---|---|---|
| `mode` | `"filesystem"` / `"explicit"` / `"hybrid"` | `"filesystem"` | Document discovery strategy. |
| `files` | `list[string]` | `[]` | Ordered list of paths relative to `paths.source`. Required when `mode = "explicit"`. |

#### Index modes

**`filesystem`** — Scribpy discovers all `*.md` files under `paths.source` recursively, in
deterministic alphabetical order.

```toml
[index]
mode = "filesystem"
```

**`explicit`** — Documents are strictly ordered by the `files` list. Only the listed files
are included. Unlisted files produce a warning.

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

**`hybrid`** — Files listed in `files` appear first in the specified order. All other
discovered files follow in alphabetical order.

```toml
[index]
mode = "hybrid"
files = [
    "index.md",
    "getting-started.md",
]
```

---

### `[document]`

Controls the assembled document output (title, table of contents, numbering).

| Key | Type | Default | Description |
|---|---|---|---|
| `title` | `string` | `null` | Document title injected as the top-level `# Heading`. |

```toml
[document]
title = "My Project — Reference Manual"
```

---

### `[document.toc]`

Controls the generated table of contents injected at the top of the assembled document.

| Key | Type | Default | Description |
|---|---|---|---|
| `enabled` | `bool` | `true` | Generate a table of contents. |
| `max_level` | `int` | `6` | Maximum heading depth included in the TOC. |
| `style` | `"bullet"` / `"numbered"` | `"bullet"` | List style used for TOC entries. |

```toml
[document.toc]
enabled = true
max_level = 3
style = "bullet"
```

!!! tip
    `max_level = 3` includes `# H1`, `## H2`, and `### H3` headings. Deeper
    headings still appear in the document body but are omitted from the TOC.

---

### `[document.numbering]`

Controls automatic section numbering applied to headings.

| Key | Type | Default | Description |
|---|---|---|---|
| `enabled` | `bool` | `true` | Apply section numbering to headings. |
| `max_level` | `int` | `6` | Maximum heading depth that receives a number. |
| `style` | `"decimal"` / `"alpha"` / `"roman"` | `"decimal"` | Numbering style. |

```toml
[document.numbering]
enabled = true
max_level = 3
style = "decimal"
```

Numbering style examples:

| Style | Example |
|---|---|
| `decimal` | `1.`, `1.1.`, `1.1.1.` |
| `alpha` | `a.`, `a.a.`, `a.a.a.` |
| `roman` | `i.`, `i.i.`, `i.i.i.` |

---

### `[builders.html]`

Controls HTML output generation.

| Key | Type | Default | Description |
|---|---|---|---|
| `mode` | `"single-page"` / `"site"` | `"single-page"` | HTML output mode. |
| `site_name` | `string` | `null` | Site name used by MkDocs (`site` mode only). |
| `theme` | `string` | `null` | MkDocs theme name (`site` mode only). |
| `output_dir` | `string` | mode-dependent | Default output directory (see below). |
| `css_files` | `list[string]` | `[]` | Additional CSS files to embed or copy. Paths relative to the project root. |

```toml
[builders.html]
mode = "site"
site_name = "Engineering Handbook"
theme = "readthedocs"
output_dir = "build/site"
css_files = ["theme/custom.css"]
```

Default output directories:

| Mode | Default `output_dir` |
|---|---|
| `single-page` | `build/html` |
| `site` | `build/site` |

A `--output-dir` CLI flag or `output_dir=` Python argument overrides the
configured value for one run without modifying `scribpy.toml`.

---

## Complete example

```toml
[project]
name = "Acme Corp Developer Guide"

[paths]
source = "docs"

[index]
mode = "explicit"
files = [
    "index.md",
    "architecture/overview.md",
    "architecture/decisions.md",
    "api/reference.md",
    "api/examples.md",
    "deployment/ci.md",
    "deployment/release.md",
]

[document]
title = "Acme Corp Developer Guide"

[document.toc]
enabled = true
max_level = 3
style = "bullet"

[document.numbering]
enabled = true
max_level = 3
style = "decimal"

[builders.html]
mode = "site"
site_name = "Acme Corp Developer Guide"
theme = "readthedocs"
output_dir = "build/site"
css_files = ["theme/acme.css"]
```
