# Software Design Description

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

