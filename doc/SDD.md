# Software Design Description

## User documentation site

### Affected modules

- `mkdocs.yml` defines site metadata, theme, plugins, Markdown extensions, and
  the complete navigation.
- `docs/` contains one English Markdown page per documentation topic.
- `pyproject.toml` isolates site build tools in the `docs` dependency group.

No module under `src/scribpy/` is changed.

### Public interfaces

The Scribpy Python and CLI interfaces are unchanged. The documentation build
interface is:

```shell
uv run --group docs mkdocs build --strict
```

### Data flow

MkDocs reads the explicit navigation and Markdown pages from `docs/`. The
The `plantuml-markdown` extension sends `plantuml` blocks to PlantUML Server
and embeds returned SVG diagrams. MkDocs Material renders the resulting page
model as a static site under `site/`.

### Error handling

Strict builds fail on invalid navigation, broken internal links, malformed
configuration, or plugin rendering errors. Network and PlantUML Server errors
are surfaced by the plugin; no fallback diagram is silently substituted.

### Test strategy

Build the site in strict mode, inspect all CLI help from the actual Click
application, execute representative CLI and Python workflows in temporary
projects, and run the repository-wide `make check` quality gate.

## Validation d'un projet

### Modules affectés

- `scribpy.core.validation.model` définit le diagnostic et le rapport publics.
- `scribpy.core.validation.engine` inspecte les manifests, adapte Mkforge et
  orchestre les diagnostics de collection.
- `scribpy.presentation.validation_console` rend le rapport avec Rich.
- `scribpy` et `scribpy.core` exportent les interfaces publiques.

### Interfaces publiques

```python
validate_project(root: str | Path) -> ProjectValidationReport
valid_report(root: str | Path, *, console: Console | None = None) -> bool
render_validation_report(report, *, console: Console | None = None) -> None
```

### Flux de données

La racine est normalisée, puis tous les manifests accessibles sont chargés et
leurs entrées `order` sont comparées aux enfants directs. En l'absence d'erreur
de manifest, `MarkdownCollection.from_tree` charge les fichiers. Chaque fichier
est envoyé à `MarkdownFile.verify`, puis les diagnostics Mkforge sont adaptés.
Les règles de collection Scribpy complètent le rapport. Le présentateur ne
reçoit ensuite que le rapport immuable.

### Gestion des erreurs

Les erreurs attendues de fichiers, de décodage et de manifest deviennent des
diagnostics bloquants. Elles ne quittent pas `validate_project`. Les erreurs de
programmation et les exceptions inattendues ne sont pas masquées.

### Stratégie de test

Les tests unitaires isolent l'inspection des manifests, l'adaptation Mkforge et
le rendu console. Les tests d'intégration créent des projets temporaires et
exécutent `validate_project` ainsi que `valid_report` sans mocker les modules
internes.
