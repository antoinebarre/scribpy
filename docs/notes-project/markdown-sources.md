# Markdown source files

Each Markdown file is one independently readable page before assembly. Give it
a page title, keep paths relative, and use ordinary ATX headings (`#` through
`######`).

## Required heading shape

A valid page starts with exactly one H1:

```markdown
# Installation

Introductory text belongs below the page title.

## Requirements

List the requirements here.

### Python

Python 3.12 or newer is required.
```

The following are invalid:

```markdown
## Installation

The first heading is not H1.
```

```markdown
# Installation

# Troubleshooting

The file contains two H1 headings.
```

Prose may appear after the H1. A file with no heading, or with prose followed
by a first H2, still fails the H1 rules.

## A complete valid example

```markdown
# Installation

Scribpy is distributed as a Python package.

## Requirements

- Python 3.12 or newer
- `uv` for dependency management

## Steps

1. Clone the repository.
2. Run `uv sync`.
3. Confirm with `uv run scribpy --version`.

See the [user guide](guide/workflow.md) for day-to-day usage and the
![architecture diagram](assets/architecture.png "High-level architecture")
below for context.
```

This file passes every source-level diagnostic: one H1 as the first heading,
no anchor fragments in links, a Markdown link target that (assuming
`guide/workflow.md` exists) resolves inside the project root, and a local
image reference that (assuming the file exists) resolves inside the project
root.

## A complete invalid example

```markdown
## Installation

Scribpy is distributed as a Python package.

# Troubleshooting

See [the FAQ](#faq) for common errors, or read
[the setup guide](../../shared/setup.md#steps).

![Missing screenshot](images/does-not-exist.png)
```

This file fails four separate diagnostics at once (its H1 count is actually
fine — exactly one — so `SOURCE_H1_COUNT_INVALID` does not fire here):

| Line | Problem | Diagnostic code |
|---|---|---|
| `## Installation` as first heading | First heading is H2, not H1 | `SOURCE_FIRST_HEADING_NOT_H1` |
| `[the FAQ](#faq)` | Anchor-only link | `LOCAL_ANCHOR_LINK` |
| `[the setup guide](../../shared/setup.md#steps)` | Cross-file link carrying an anchor fragment, and escaping the collection root | `LOCAL_ANCHOR_LINK` and `INTERNAL_MARKDOWN_LINK_OUTSIDE_ROOT` |
| `images/does-not-exist.png` | Local image file does not exist | `LOCAL_IMAGE_MISSING` |

## Understand heading shifting

The assembled document reserves H1 for the project. A root page's source H1
therefore becomes H2. Each containing folder adds another heading level.

| Source location | Source H1 becomes | Deepest safe source heading |
|---|---:|---:|
| Project root | H2 | H5 becomes H6 |
| One folder deep | H3 | H4 becomes H6 |
| Two folders deep | H4 | H3 becomes H6 |
| Three folders deep | H5 | H2 becomes H6 |

If a shifted heading would exceed H6, `HEADING_LEVEL_OVERFLOW` blocks the
build. Prefer a shallower project tree or fewer heading levels inside the page.

The shift amount is `2 + <folder depth>`: a root-level file uses base level 2
(so its `#` becomes `##`); a file one folder deep uses base level 3, and so
on. A heading's final level is `min(6, base_level + source_level - 1)` for
every case except when that value would exceed 6, in which case the build
fails outright rather than silently clamping the heading — clamping would
make deeply nested distinct headings collapse to the same level.

## Content Scribpy preserves

Normal paragraphs, emphasis, lists, tables, quotes, inline code, and fenced
code remain Markdown content. Scanners ignore apparent headings and image/link
syntax inside fenced code:

````markdown
# API example

```python
text = "# This is code, not a heading"
```
````

PlantUML and Mermaid fences are the exception: the build pipeline renders them
as generated PNG images. Select their backends in the root manifest.

## Summary of source-level validation rules

These eight rules run during `scribpy validate`, `scribpy build`, and
`mkdocs-export`. All are implemented in `scribpy.core.diagnostics.rules` as
independent `CollectionDiagnosticRule` strategies; the engine adds new checks
by adding new rule modules, not by editing existing ones.

| Code | Severity | Triggers when |
|---|---|---|
| `SOURCE_FIRST_HEADING_NOT_H1` | ERROR | A file's first heading exists and is not H1. |
| `SOURCE_H1_COUNT_INVALID` | ERROR | A file has zero H1 headings, or more than one. |
| `HEADING_LEVEL_OVERFLOW` | ERROR | A heading would exceed H6 once shifted by folder depth. |
| `INTERNAL_MARKDOWN_LINK_MISSING` | ERROR | A link targets a `.md`/`.markdown` file that does not exist. |
| `INTERNAL_MARKDOWN_LINK_OUTSIDE_ROOT` | ERROR | A link targets a Markdown file outside the collection root. |
| `LOCAL_ANCHOR_LINK` | ERROR | Any link target contains `#`, whether alone (`#section`) or appended to a file (`page.md#section`). |
| `LOCAL_IMAGE_MISSING` | ERROR | A local image reference's file does not exist on disk. |
| `IMAGE_OUTSIDE_ROOT` | ERROR | A local image reference resolves outside the collection root. |
| `EXTERNAL_IMAGE_REFERENCE` | WARNING | An image reference points to an external URL. |

`concatenate()` only blocks the build on `ERROR`-severity diagnostics.
Warnings (currently only `EXTERNAL_IMAGE_REFERENCE`, plus manifest warnings
described in [Project structure](index.md)) are reported but do not stop
assembly. See [Links and images](links-and-images.md) for link/image rule
details and [Root manifest](root-manifest.md) / [Folder manifests and
order](folder-manifests.md) for manifest-level errors.

## Recommended page checklist

Before adding a page to `order`, confirm that it:

1. is UTF-8 text with a recognized Markdown suffix;
2. has exactly one H1 and uses it as the first heading;
3. uses relative links to existing pages without `#` fragments;
4. uses local images inside the project whenever possible;
5. does not exceed H6 after its folder depth is added.

Then run `scribpy validate PROJECT`.
