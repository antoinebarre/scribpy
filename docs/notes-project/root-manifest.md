# Root manifest

The root `scribpy.yml` has three top-level concerns: descriptive project
metadata, global build settings, and direct-child order. It is the *only*
manifest that carries `project` and `build` — every other manifest in the
tree is a [folder manifest](folder-manifests.md) limited to `title` and
`order`.

If no root `scribpy.yml` exists at all, Scribpy falls back to defaults for
every setting below and traverses the root directory alphabetically.

## Complete annotated example

```yaml
project:
  title: Team Handbook       # Used for the assembled H1 and MkDocs site name.
  author: Documentation Team # Preserved metadata; not interpreted by assembly.
  version: 1.0.0             # Preserved metadata; any YAML value is accepted.

build:
  toc: true                  # Insert a TOC in single-document output.
  toc_depth: 3               # Include H2 through H4 in that TOC.
  heading_numbering:
    enabled: true            # Number assembled headings with MkForge.
  plantuml_backend: plantuml_server
  plantuml_server_url: https://www.plantuml.com/plantuml
  mermaid_backend: kroki
  mermaid_command: mmdc

order:
  - index.md
  - guide/
```

## `project`

`project` is a string-keyed mapping. Scribpy specifically reads `title` for
the assembled document title and exported MkDocs site name. Other values such
as `author` and `version` are retained but do not change assembly behavior. If
`title` is missing or empty, Scribpy uses the root directory name.

## Every `build` option

| Key | Type | Default | Meaning |
|---|---|---|---|
| `toc` | strict boolean | `false` | Insert a Markdown TOC after the assembled H1. |
| `toc_depth` | integer ≥ 1 | `3` | Number of levels below H1 included in the TOC. Boolean values are rejected. |
| `heading_numbering` | mapping or null | absent | Configure heading numbering. Numbering is disabled when the block is absent. |
| `heading_numbering.enabled` | strict boolean | `true` when block exists | Enable or disable MkForge numbering. |
| `plantuml_backend` | string | `plantuml_server` | `plantuml_server`, `kroki`, `web`, or `local`. |
| `plantuml_server_url` | absolute HTTP(S) URL | `https://www.plantuml.com/plantuml` | Server used only by `plantuml_server`; trailing slash is normalized away. |
| `mermaid_backend` | string | `kroki` | `kroki`, `web`, `mermaid_cli`, or `local`. |
| `mermaid_command` | non-empty string | `mmdc` | Executable name/path used by Mermaid CLI rendering. |

`web` is a compatibility alias for Kroki for both diagram types. Mermaid
`local` aliases `mermaid_cli`. PlantUML `local` is not functional: rendering
always raises `NotImplementedError`.

The `build` model rejects unknown keys — a typo such as `tocs: true` fails
manifest loading with `InvalidScribpyManifestError` rather than being
silently ignored. By contrast, an unknown *top-level* root key (something
other than `project`, `build`, or `order`) produces `ScribpyManifestWarning`
and is ignored, so `notes: draft` at the top level warns but does not fail.

### `toc` and `toc_depth` in practice

`toc_depth` counts levels *below the assembled H1*, not raw Markdown heading
numbers. A depth of `1` includes only H2 entries; `2` includes H2 and H3; the
default `3` includes H2 through H4. Since a root-level source page's H1 is
itself shifted to H2 (see [Markdown source files](markdown-sources.md)), the
default `toc_depth: 3` is usually enough to list every page title (H2) and
every one of that page's top two heading levels (H3, H4) without descending
into deeply nested subsections.

If no heading falls within the configured depth, the TOC transform leaves the
document unchanged rather than inserting an empty list.

### `heading_numbering`

```yaml
build:
  heading_numbering:
    enabled: true
```

Numbering is off by default: the block must be present, and its `enabled`
field must be `true` (the field itself defaults to `true` once the block
exists, so `heading_numbering: {}` also enables it). Omitting `heading_numbering`
entirely, or omitting the whole `build` key, leaves numbering disabled.
Numbering runs through MkForge and, when active, changes every downstream
anchor computed by link rewriting and the TOC — see [Links and
images](links-and-images.md) for the exact rewritten-anchor example.

## `order`

`order` is a list of direct-child names. A directory may include or omit its
trailing slash. Never put `guide/page.md` in the root order; list `guide/`, then
control that directory with `guide/scribpy.yml`.

When `order` is absent or empty, children are traversed alphabetically. When it
is present with entries, listed children are traversed in order, missing
entries are errors, and unlisted children are warned about and ignored. See
[Project structure](index.md) for the full traversal algorithm shared by root
and folder manifests.

## Minimal configurations

Defaults with a title and explicit page order:

```yaml
project:
  title: Notes
order:
  - index.md
```

TOC without heading numbering:

```yaml
project:
  title: Notes
build:
  toc: true
  heading_numbering:
    enabled: false
order: [index.md]
```

Self-hosted PlantUML Server and local Mermaid rendering (no network
dependency for either diagram type once `mmdc` is installed):

```yaml
project:
  title: Internal Architecture Notes
build:
  plantuml_backend: plantuml_server
  plantuml_server_url: https://plantuml.internal.example.com
  mermaid_backend: mermaid_cli
  mermaid_command: /opt/mermaid/bin/mmdc
order:
  - index.md
  - architecture/
```
