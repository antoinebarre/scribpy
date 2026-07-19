# Scribpy

Scribpy assembles a directory of small Markdown notes into publishable output.
It is for writers who want source files that stay easy to edit while manifests
control their order. Scribpy validates the collection, rewrites cross-file
links, renders diagrams, collects images, and can produce one Markdown file,
one standalone HTML page, or a MkDocs input tree.

Scribpy is not a Markdown editor, web CMS, PDF renderer, or hosting service. It
does not deploy a site. Network-backed diagram providers also remain external
services.

## Why a separate assembler at all

Most Markdown documentation tools force a choice: keep pages small and
independently navigable (a static-site generator like plain MkDocs), or
merge everything into one file for a single deliverable (manual copy-paste,
or a pandoc-style concatenation script). Scribpy keeps the source split
into small, independently editable files — the unit a writer actually
edits and reviews — while still producing whichever shape a reader needs:
one merged Markdown file, one standalone HTML page, or a page-per-file
MkDocs input tree, all from the same source and the same `scribpy.yml`
manifests. You write once; you choose the output shape per audience.

## Documentation map

This site follows a fixed path, and each section builds on the last:

1. **[Architecture](architecture/index.md)** — the domain model and pipeline
   design, useful before extending Scribpy or reasoning about its
   guarantees.
2. **[Organizing a notes project](notes-project/index.md)** — how to lay
   out a project on disk: source rules, links, manifests.
3. **[Using the CLI](cli/index.md)** — the `scribpy` command, for everyday
   authoring workflows and CI.
4. **[Using the Python API](python-api/index.md)** — the `scribpy` package,
   for programmatic workflows and custom rules/renderers.
5. **[Guides](guides/outputs.md)** — task-oriented recipes and
   troubleshooting once you already know the concepts.
6. **[Reference](reference/cli.md)** — exhaustive, example-backed lookup
   tables for every command and every public API name.

If you are new to Scribpy, read
[Installation](getting-started/installation.md) and
[Core concepts](getting-started/concepts.md) next, then follow the smallest
useful example below.

## Smallest useful example

```text
handbook/
├── scribpy.yml
├── intro.md
└── install.md
```

```yaml title="handbook/scribpy.yml"
project:
  title: Team Handbook
order: [intro.md, install.md]
```

```markdown title="handbook/intro.md"
# Welcome

Continue with [installation](install.md).
```

```markdown title="handbook/install.md"
# Installation

Run `uv sync`.
```

```shell
scribpy validate handbook
scribpy build handbook build/handbook.md
```

The result is one document headed `Team Handbook`, followed by the shifted
source headings. The link to `install.md` becomes a link to the assembled
heading anchor.

## Where to go next

- Follow the [complete CLI tutorial](cli/demo.md) to build Markdown, HTML, and
  MkDocs outputs step by step.
- Follow the [complete Python tutorial](python-api/demo.md) for an executable
  application workflow.
- Read [links and images](notes-project/links-and-images.md) before moving
  assets or pages.
- Use the [CLI reference](reference/cli.md) when you only need exact arguments
  and defaults.
