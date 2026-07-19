# Manifest reference

Every Scribpy project and every folder inside it can carry a `scribpy.yml`
manifest. Manifests are plain UTF-8 YAML mappings, loaded by
`scribpy.core.manifest.load_root_manifest` (root) and
`load_folder_manifest` (folder), and validated with Pydantic models that
reject unknown shapes early rather than failing silently later in the
pipeline. There are exactly two manifest shapes: the **root** manifest,
which carries project metadata and build policy, and the **folder**
manifest, which is deliberately limited to a title and a child order.

This page is the exhaustive field-by-field reference. For a narrative,
example-driven walkthrough, read
[Root manifest](../notes-project/root-manifest.md) and
[Folder manifests and order](../notes-project/folder-manifests.md) first.

## Root schema

| Key | Type | Required | Default | Validation |
|---|---|---:|---|---|
| `project` | mapping with string keys | no | `{}` | Non-mapping is invalid. |
| `build` | `BuildSettings` mapping | no | all build defaults | Unknown nested keys are invalid. |
| `order` | list of strings | no | `[]` | Each normalized item must be one direct child name. |

Unknown root keys emit `ScribpyManifestWarning` and are ignored. YAML `null`
for `project`, `build`, or `order` is treated like absence where supported by
the loader.

A minimal root manifest is valid on its own:

```yaml
project:
  title: Engineering Handbook
```

Every field below defaults sensibly, so this three-line file is enough to
start a project. Add `build` and `order` only when you need to override a
default or fix traversal sequence.

## Project metadata

`project` accepts arbitrary string keys and object values. Assembly reads:

| Key | Used by | Fallback |
|---|---|---|
| `title` | assembled H1 and MkDocs export site name | project directory name |

`init_skeleton` also writes `author` when non-empty and always writes
`version`. They remain metadata and do not alter the assembly pipeline.

```yaml
project:
  title: Engineering Handbook
  author: Platform Team
  version: "2.1.0"
```

`author` and `version` are stored for humans and downstream tooling; nothing
in Scribpy's pipeline reads them back. Only `title` changes generated output.

## Build settings

The `build` mapping controls the assembly pipeline described in
[Assembly pipeline](../architecture/assembly-pipeline.md): heading
numbering, link rewriting, TOC insertion, and diagram rendering all read
their configuration from here. Every key is optional; omitting `build`
entirely is equivalent to accepting every default in the table below.

A fully annotated example, with every key set explicitly:

```yaml
build:
  toc: true                 # insert a table of contents after the H1
  toc_depth: 2               # TOC includes H2 and H3, not H4+
  heading_numbering:
    enabled: true             # delegate numbering to MkForge
  plantuml_backend: plantuml_server
  plantuml_server_url: https://www.plantuml.com/plantuml
  mermaid_backend: kroki
  mermaid_command: mmdc
```

| Key | Model type | Default | Accepted values / constraints |
|---|---|---|---|
| `toc` | strict `bool` | `false` | `true` or `false`; strings and integers are rejected. |
| `toc_depth` | strict `int` | `3` | At least 1; boolean rejected before integer validation. |
| `heading_numbering` | mapping or null | `null` | Contains only `enabled`. |
| `heading_numbering.enabled` | strict `bool` | `true` inside an existing block | `true` or `false`. Overall numbering is false when block is absent/null. |
| `plantuml_backend` | `str` | `plantuml_server` | Factory accepts `plantuml_server`, `kroki`, `web`, `local`. Unknown value fails when renderer is created. |
| `plantuml_server_url` | `str` | `https://www.plantuml.com/plantuml` | Absolute `http` or `https` URL with host; trailing slash removed. |
| `mermaid_backend` | `str` | `kroki` | Factory accepts `kroki`, `web`, `mermaid_cli`, `local`. |
| `mermaid_command` | non-empty `str` | `mmdc` | Trimmed; empty/whitespace-only value invalid. |

Notes on interaction between keys:

- `heading_numbering` absent or `null` disables numbering entirely, even
  though `enabled` would default to `true` if the block existed. This is a
  common surprise: writing `heading_numbering: {}` (an empty but present
  block) turns numbering **on**, while omitting the key entirely leaves it
  **off**. See [Common recipes](../guides/recipes.md) for the explicit-off
  form.
- `toc_depth` only matters when `toc: true`; it is still validated even if
  `toc` is `false`, so an invalid `toc_depth` fails manifest loading
  regardless of whether a TOC is requested.
- `plantuml_backend` and `mermaid_backend` are validated lazily: an unknown
  string does not fail at manifest-load time, only when
  `scribpy.core.plantuml.make_renderer` or
  `scribpy.core.mermaid.make_renderer` is called during assembly. See
  [Diagram renderers](../architecture/diagram-renderers.md) for the full
  backend list and the `local`/`web` aliases.
- `plantuml_server_url` is used only by the `plantuml_server` backend; it is
  still validated even if a different backend is configured.
- `mermaid_command` is used only by the `mermaid_cli`/`local` backend; it
  is still validated even if `kroki` is configured.

## Folder schema

| Key | Type | Required | Default | Effect |
|---|---|---:|---|---|
| `title` | string or null | no | `null` | Folder heading/navigation label override. |
| `order` | list of strings | no | `[]` | Direct-child traversal. |

Unknown folder keys warn and are ignored. A non-string title or malformed
order raises `InvalidScribpyManifestError`.

A folder manifest never carries `build` or `project` — those belong only at
the root. A typical folder manifest is short:

```yaml
title: Architecture
order:
  - overview.md
  - domain-model.md
  - decisions.md
```

Without a `title`, Scribpy derives a folder heading from the directory name
(see [Folder manifests and order](../notes-project/folder-manifests.md)).
Without `order`, Markdown files and subfolders are traversed alphabetically.

## Order normalization

Each string is stripped and has trailing `/` removed before validation.
Accepted examples:

```yaml
order:
  - index.md
  - guide
  - assets/
```

Rejected examples:

```yaml
order:
  - guide/page.md  # not a direct name
  - ..             # parent traversal
  - .              # current directory
  - ""             # empty
```

A listed child must exist and be a supported Markdown file or directory. With
a non-empty explicit order, supported unlisted children warn and are ignored.
Without explicit entries, supported children are traversed alphabetically.

## Error representation

Malformed YAML, invalid mapping shape, bad key type, bad order entry, invalid
build model, and missing ordered child are surfaced as
`InvalidScribpyManifestError`. Its public attributes are:

```python
try:
    collection = scribpy.MarkdownCollection.from_tree(root)
except scribpy.InvalidScribpyManifestError as error:
    print(error.path)
    print(error.detail)
```

