# Report Generator — Requirements

## Vision

Fournir une API Python programmatique permettant de **construire** des rapports Markdown (GitHub Flavored Markdown) par code, à l'image du MATLAB Report Generator. L'utilisateur compose un rapport en assemblant des objets (`Report`, `Chapter`, `Section`, `Paragraph`, etc.) puis exporte le résultat en GFM.

---

## REQ-RG-001 — Point d'entrée principal

La feature expose une classe `Report` instanciable directement par l'utilisateur, sans configuration de projet (`scribpy.toml`) requise.

```python
from scribpy.report import Report, Chapter, Section, Paragraph, Text, CodeBlock, Table

report = Report(title="My Report")
```

---

## REQ-RG-002 — Modèle de contenu hiérarchique (conteneurs imbriqués)

Le rapport est un arbre de **conteneurs** et de **feuilles** :

| Classe | Rôle | Enfants autorisés |
|---|---|---|
| `Report` | Racine du document | `Chapter` |
| `Chapter` | Niveau 1 (H1) | `Section`, éléments feuilles |
| `Section` | Niveau N (H2…H6) | `Section` (imbrication), éléments feuilles |
| `Paragraph` | Bloc de texte | éléments inline |

L'imbrication de `Section` dans une `Section` **incrémente automatiquement** le niveau de heading (H2 → H3 → …) sans que l'utilisateur ait à spécifier `level=`. Le niveau maximal est H6 ; toute imbrication au-delà lève une `ReportDepthError`.

---

## REQ-RG-003 — Éléments feuilles (contenu GFM)

Les éléments feuilles suivants doivent être supportés en première version :

| Classe | GFM produit |
|---|---|
| `Paragraph` | Bloc de texte brut ou inline-formaté |
| `Text` | Inline : bold, italic, inline-code, strikethrough |
| `CodeBlock` | Bloc de code fencé avec language hint |
| `Table` | Tableau GFM (`\|` syntax) avec header obligatoire |
| `BulletList` | Liste non ordonnée (`-`) |
| `NumberedList` | Liste ordonnée (`1.`) |
| `Image` | `![alt](path)` |
| `HorizontalRule` | `---` |
| `BlockQuote` | `>` |

> **Note `Table` :** Le GFM impose une ligne de séparation `|---|---|` entre le header et le corps. Un tableau sans header n'est pas du GFM valide — le header est donc obligatoire.

---

## REQ-RG-004 — API de composition fluide

Chaque conteneur expose une méthode `add(*items)` qui retourne `self` pour permettre le chaînage :

```python
report = (
    Report(title="Status Report")
    .add(
        Chapter(title="Introduction")
        .add(Paragraph("Context of the study."))
        .add(
            Section(title="Scope")
            .add(Paragraph("This covers Q1 2026."))
            .add(
                Section(title="Exclusions")
                .add(Paragraph("Legacy systems are excluded."))
            )
        )
    )
)
```

---

## REQ-RG-005 — Numérotation automatique des sections

Option au niveau `Report` : `auto_numbering: bool = False`. Lorsqu'activée, les headings sont préfixés automatiquement (`1.`, `1.1.`, `1.1.1.`, …) lors du rendu, sans modifier les titres stockés dans les objets.

---

## REQ-RG-006 — Génération de Table des matières

Option au niveau `Report` : `toc: bool = False`. Lorsqu'activée, une TOC GFM (liste de liens ancre) est insérée après le titre du rapport et avant les chapitres.

---

## REQ-RG-007 — Export vers une chaîne ou un fichier

```python
# Rendu en string
md_string: str = report.render()

# Écriture directe
report.save("output/report.md")
```

`render()` retourne du GFM valide. `save()` crée les répertoires intermédiaires si nécessaires.

---

## REQ-RG-008 — Intégration dans le pipeline existant

`Report.save()` produit un fichier `.md` que le pipeline `scribpy` existant peut ensuite ingérer via `build_html()` ou `build_markdown()` sans modification. Aucun couplage fort avec `ProjectPipeline` n'est requis en v1.

---

## REQ-RG-009 — Validation et erreurs explicites

| Situation | Exception |
|---|---|
| Imbrication > H6 | `ReportDepthError` |
| `Table` avec 0 colonnes | `InvalidTableError` |
| Type d'enfant non autorisé dans un conteneur | `InvalidChildError` |
| Titre de `Report`/`Chapter`/`Section` vide | `ValueError` |

Les erreurs sont levées **à l'ajout** (fail-fast), pas au rendu.

---

## REQ-RG-010 — Respect des standards du projet

- Dataclasses pour les modèles de données, fonctions pour la logique de rendu
- Full type hints
- Cyclomatic complexity < 5 par fonction
- Pas d'héritage : composition + injection
- Module dédié : `scribpy/report/`
