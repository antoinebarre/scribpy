# Scribpy

Scribpy assembles a directory of small Markdown notes into publishable
output. It is for writers who want source files that stay easy to edit
while `scribpy.yml` manifests control their order. Scribpy validates the
collection, rewrites cross-file links, renders PlantUML and Mermaid
diagrams, collects images, and produces one Markdown file, one standalone
HTML page, or a MkDocs input tree — all from the same source.

Scribpy is not a Markdown editor, web CMS, PDF renderer, or hosting
service. It does not deploy a site.

Full documentation: **https://antoinebarre.github.io/scribpy/**

## Installation

Scribpy requires Python 3.12 or newer.

```shell
pip install scribpy
```

For contributors and local evaluation, clone the repository and use
[uv](https://docs.astral.sh/uv/):

```shell
uv sync
uv run scribpy --version
```

## Quick example

```text
handbook/
├── scribpy.yml
├── intro.md
└── install.md
```

```yaml
# handbook/scribpy.yml
project:
  title: Team Handbook
order: [intro.md, install.md]
```

```markdown
# handbook/intro.md
# Welcome

Continue with [installation](install.md).
```

```shell
scribpy validate handbook
scribpy build handbook build/handbook.md
```

The result is one document headed `Team Handbook`, followed by the shifted
source headings, with the link to `install.md` rewritten to the matching
assembled heading anchor.

## What Scribpy can produce

| Command | Output |
|---|---|
| `scribpy build` | One assembled Markdown file |
| `scribpy html` | A standalone, self-contained HTML page |
| `scribpy mkdocs-export` | A page-per-file MkDocs input tree |

## Documentation

- [Getting started](https://antoinebarre.github.io/scribpy/getting-started/installation/)
- [Organizing a notes project](https://antoinebarre.github.io/scribpy/notes-project/)
- [Using the CLI](https://antoinebarre.github.io/scribpy/cli/)
- [Using the Python API](https://antoinebarre.github.io/scribpy/python-api/)
- [Reference](https://antoinebarre.github.io/scribpy/reference/cli/)

## Development

```shell
uv sync
make check
```

`make check` runs the full quality gate: formatting, linting, type
checking, security scanning, and tests with coverage. See
[CLAUDE.md](CLAUDE.md) for the complete contributor guide.

## License

No license file is currently published for this repository. All rights
reserved unless a license is added.
