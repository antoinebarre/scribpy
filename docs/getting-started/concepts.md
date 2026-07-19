# Core concepts

Understanding five concepts prevents most Scribpy mistakes.

## Project

A project is one root directory containing Markdown pages, optional assets,
and usually a root `scribpy.yml`. The root is the argument passed to
`validate`, `diagnose`, `build`, and `mkdocs-export`.

```text
handbook/                 <- project root
├── scribpy.yml           <- global metadata, build policy, root order
├── index.md              <- one source page
├── assets/               <- local project resources
└── guide/
    ├── scribpy.yml       <- local title and local order
    └── installation.md   <- another source page
```

## Source page

A source page is a UTF-8 Markdown file with exactly one H1, used as its page
title. Source pages remain independently readable. They use paths relative to
their own directory.

Scribpy does not treat one file as a master document. The collection and its
manifests determine the whole project.

## Manifest

A manifest is configuration at one directory boundary:

- the root manifest additionally owns project metadata and global build
  settings;
- a folder manifest owns only its display title and direct-child order;
- order never reaches through multiple directory levels.

Manifests decide which Markdown pages belong to the ordered collection. An
unlisted page can exist on disk without being assembled.

## Collection

`MarkdownCollection` is the resolved, ordered tuple of pages plus the root
manifest. Loading a collection performs filesystem discovery and manifest
ordering. It does not yet write output.

```python
collection = scribpy.MarkdownCollection.from_tree("handbook")
for page in collection.files:
    print(page.path)
```

## Assembly and export

Assembly merges the collection into one Markdown document and applies global
transforms. Export selects a presentation target.

| Operation | Reads | Writes | Keeps pages separate? |
|---|---|---|---:|
| `MarkdownCollection.from_tree` | Project | Nothing | yes, in memory |
| `concatenate` / CLI `build` | Loaded collection | Markdown + assets | no |
| `html_export` / CLI `html` | Assembled Markdown | HTML | no |
| `mkdocs_export` | Source project | MkDocs input tree | yes |

The distinction matters: `html` takes an assembled Markdown file, while
`mkdocs-export` takes the original project root.

## Validation and diagnostics

Validation is the broad project quality gate. Diagnostics are focused rules on
the resolved collection. Both produce findings with severities:

- `error` blocks validity and usually assembly;
- `warning` allows output but identifies a publication risk;
- `info` is non-blocking context.

Generated files are never the source of truth. Fix the project, validate it,
and regenerate output.

