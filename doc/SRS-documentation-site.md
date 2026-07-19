# SRS — Documentation site

## Requirements

- **REQ-DOCS-01** — The repository SHALL provide an English MkDocs Material
  site whose source is stored under `docs/` and whose explicit navigation is
  configured by the root `mkdocs.yml`.
  - Acceptance criterion: `uv run --group docs mkdocs build --strict` builds
    the complete site without warnings.
- **REQ-DOCS-02** — The site SHALL explain the project scope, architecture,
  notes-project format, CLI, Python API, and references in that order.
  - Acceptance criterion: each subject has a dedicated navigation section and
    short topic-focused pages.
- **REQ-DOCS-03** — Every documented CLI command and Python interface SHALL
  match the current implementation.
  - Acceptance criterion: all seven command help pages are checked against
    `scribpy.cli.main`, and the API reference covers every name in
    `scribpy.__all__` with an example.
- **REQ-DOCS-04** — Architecture and workflow diagrams SHALL be authored as
  PlantUML and rendered during the MkDocs build.
  - Acceptance criterion: the site contains class, sequence, activity, and
    project-tree diagrams in `plantuml` fences processed by
    `plantuml-markdown`.
- **REQ-DOCS-05** — The documentation SHALL distinguish implemented behavior,
  optional external services, and placeholders.
  - Acceptance criterion: the local PlantUML backend is explicitly described
    as unimplemented and no example presents it as functional.
- **REQ-DOCS-06** — The repository SHALL isolate documentation tooling from
  Scribpy runtime dependencies.
  - Acceptance criterion: MkDocs Material and the PlantUML plugin are declared
    only in the `docs` dependency group.
- **REQ-DOCS-07** — The task SHALL NOT configure GitHub Pages deployment.
  - Acceptance criterion: no workflow or deployment command is added.
