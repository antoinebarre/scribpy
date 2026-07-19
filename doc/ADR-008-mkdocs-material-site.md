# ADR-008 — Build the documentation with Material and plantuml-markdown

## Context

Scribpy has accurate internal architecture records but no user-facing,
navigable documentation site. The requested site must be buildable locally,
ready for a later GitHub Pages workflow, and must render the existing PlantUML
diagrams without introducing a local Java or Node toolchain.

## Decision

Store documentation pages in the conventional `docs/` directory and configure
the site from a root `mkdocs.yml` with an explicit navigation tree. Use
MkDocs Material as the presentation theme and `plantuml-markdown` as the
Python-Markdown PlantUML extension. Configure the extension to render
`plantuml` fenced blocks as SVG through the public PlantUML Server.

Declare `mkdocs-material` and `plantuml-markdown` in a dedicated `docs`
dependency
group. They are authoring and build tools, not Scribpy runtime dependencies.
Keep diagrams next to the prose that explains them so each page remains a
self-contained documentation source.

## Consequences

- The documentation has search, responsive navigation, code highlighting, and
  a deterministic local build command.
- Diagram builds require network access to the configured PlantUML Server.
- Documentation dependencies do not increase the installed Scribpy package.
- Diagram source remains reviewable as text and can adapt the diagrams in
  `doc/architecture-core.md`.
- GitHub Pages deployment remains a separate decision and task.

## Alternatives rejected

| Alternative | Reason rejected |
|---|---|
| Plain MkDocs theme | It does not provide the requested Material experience. |
| Pre-rendered diagram images | They drift from source and make reviews harder. |
| Local PlantUML JAR | It adds a Java installation requirement solely for docs. |
| Mermaid for documentation diagrams | The request requires PlantUML and the existing architecture already uses it. |
| Runtime dependencies | Site tooling is unrelated to using Scribpy as a library or CLI. |
