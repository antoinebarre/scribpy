# ADR-0008 — Introduction d'un module `scribpy/report/` pour le Report Generator

**Date:** 2026-05-20
**Statut:** propose
**Decideurs:** Antoine Barre
**References:** `doc/user-manual/report-generator.md`, `doc/SDD.md`, `doc/adr/ADR-0005-phase-5-first-build-artifact-markdown.md`

---

## Contexte

`scribpy` dispose d'un pipeline robuste pour **transformer** des fichiers `.md` existants. Il n'existe pas d'API pour **générer programmatiquement** un document Markdown de zéro, équivalente au MATLAB Report Generator. Cette capacité est demandée pour des cas d'usage où le contenu est produit dynamiquement (résultats de calcul, rapports d'audit, synthèses automatisées).

---

## Décision

Créer un module `scribpy/report/` autonome exposant un arbre d'objets composables (`Report`, `Chapter`, `Section`, …) et un renderer GFM pur.

**Layout prévu :**

```
scribpy/report/
├── __init__.py          # exports publics
├── nodes.py             # dataclasses Report, Chapter, Section, Paragraph, feuilles
├── renderer.py          # render(node) → str  (fonctions pures)
├── toc.py               # generate_toc(Report) → str
├── numbering.py         # apply_numbering(headings) → str[]
├── validation.py        # validate_child(parent, child) + erreurs custom
└── errors.py            # ReportDepthError, InvalidTableError, InvalidChildError
```

---

## Alternatives considérées

| Alternative | Raison du rejet |
|---|---|
| Étendre `Document` existant | `Document` est un modèle **parsé** (immutable, issu d'un fichier). L'ajouter en mode « écriture » crée une dualité de responsabilité contraire au SRP. |
| Générer du HTML directement | Hors scope : la demande est un format GFM. HTML reste l'affaire des exporters existants. |
| Bibliothèque externe (mdutils, mistune-generate) | Perte de contrôle sur le modèle d'objet et les conventions du projet ; dépendance externe inutile. |
| Unique classe `Node` générique | Valide conceptuellement, mais masque la sémantique métier (un `Chapter` n'est pas une `Section` générique) et complique la validation des enfants autorisés. |

---

## Conséquences

**Positives :**

- Module totalement découplé du pipeline existant — peut évoluer indépendamment
- L'output est un `.md` standard que le pipeline existant consomme sans modification
- Respecte SOLID : chaque classe a un rôle unique, la logique de rendu est séparée des données
- Extensible : ajouter un `XmlRenderer` ou `HtmlRenderer` en v2 ne touche pas aux nodes

**Négatives / Risques :**

- Duplication partielle avec `transforms/markdown.py` (numérotation, TOC) — à surveiller pour éventuelle mutualisation en v2
- Pas de round-trip : un `.md` parsé ne se re-transforme pas automatiquement en arbre `Report` (hors scope v1)

---

## Règles d'implémentation

1. Les nodes sont des **dataclasses** (`frozen=False` pour permettre `add()`, mais sans mutabilité publique sauvage)
2. Le renderer est un ensemble de **fonctions pures** dispatching sur le type du node (`match` / `isinstance`)
3. La profondeur de heading est calculée **à la traversée** (contexte passé en paramètre), pas stockée dans les nodes
4. `add()` retourne `self` pour le chaînage mais **valide immédiatement** le type de l'enfant
5. `render()` et `save()` sont les seuls points d'entrée publics pour la génération
