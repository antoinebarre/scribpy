---
type: roadmap
status: draft
date: 2026-06-21
tags: [architecture, planning, scribpy]
---

# Plan de bataille — Développement Scribpy

Découpage en lots incrémentaux. Chaque lot est livrable et testable seul (`pytest` vert, pas de fonctionnalité bloquante en suspens). L'ordre suit la dépendance réelle entre fonctionnalités : le pipeline de transformation commun (lot 1-2) est un prérequis dur pour tout le reste ; HTML page unique avant site (la navigation multi-pages réutilise le renderer de page) ; PDF après HTML (le besoin TOC/bookmarks PDF est plus simple si le modèle de titres est déjà stabilisé par le cas HTML).

## Lot 0 — Socle du projet

- Initialisation `uv init`, `pyproject.toml` (PEP 621), `hatchling`, structure `src/scribpy/`.
- Configuration `ruff`, `mypy` (strict), `pytest` + `pytest-cov`.
- `config.py` : dataclasses figées de configuration (`ScribpyConfig`, seuils, chemins par défaut) — aucune valeur magique ailleurs dans le code.
- Hiérarchie d'exceptions (`ScribpyError` et sous-classes) — seule hiérarchie de classes du projet, exception justifiée (cf. Conception).
- **Sortie** : squelette installable (`uv add .`), CI locale (lint + types + tests vides) verte.

## Lot 1 — Pipeline de parsing Markdown (cœur partagé)

- `core/document.py` : `ParsedDocument`, `Heading`, `ImageRef` (dataclasses).
- `core/markdown_parser.py` : Markdown texte → `ParsedDocument` via `markdown-it-py`.
- Tests unitaires sans I/O disque (texte en mémoire → structure).
- **Exigences couvertes** : socle de REQ-001, REQ-009, REQ-012, REQ-015 (tous les formats de sortie dépendent de ce parsing).
- **Sortie** : `parse(markdown_text: str) -> ParsedDocument` fonctionnel et testé isolément (REQ-021).

## Lot 2 — Résolution d'images et diagrammes (double mode web/hors-ligne)

- `core/image_resolver.py` : vérification d'existence (REQ-004), collecte d'avertissements sans interruption (REQ-018).
- `diagrams/render_mode.py` : `RenderMode` (Enum WEB/OFFLINE) et intégration dans `ScribpyConfig` (réglage global, REQ-024).
- `core/diagram_renderer.py` (Protocol) + dispatch à clé composite `(engine, mode)`.
- `diagrams/plantuml_offline.py` (subprocess `.jar`), `diagrams/mermaid_offline.py` (`mmdc`).
- `diagrams/plantuml_web.py`, `diagrams/mermaid_web.py` (appels `httpx` vers le serveur PlantUML public et `mermaid.ink`), avec erreur explicite et fail-fast sur échec réseau, sans repli automatique (REQ-025).
- Décision actée : ADR-002 (remplace ADR-001).
- Tests unitaires : dispatch testé avec de faux renderers (pas d'invocation réelle des quatre implémentations dans la suite par défaut) ; `plantuml_offline`/`mermaid_offline` testés avec `.jar`/`mmdc` factices ; `plantuml_web`/`mermaid_web` testés avec un client HTTP mocké (succès et échec réseau simulé) — seul point du projet où un mock réseau est nécessaire, isolé à ces deux modules.
- **Exigences couvertes** : REQ-005, REQ-006, REQ-018, REQ-023, REQ-024, REQ-025.
- **Sortie** : un `ParsedDocument` enrichi, images vérifiées, blocs de diagramme remplacés par des références SVG, mode actif respecté sans fallback silencieux.

## Lot 3 — Export HTML page unique (F1)

- `render/html_renderer.py` : `ParsedDocument` → HTML autonome.
- Application CSS utilisateur (REQ-002).
- `render/toc_widget.py` : génération du menu hamburger JS, activable/désactivable (REQ-003).
- Gestion du répertoire de sortie et copie des assets associés (REQ-007).
- **Exigences couvertes** : REQ-001, REQ-002, REQ-003, REQ-007, REQ-019 (mesure de performance sur fichier de référence).
- **Sortie** : CLI `scribpy export html input.md --css style.css --toc --output dist/` fonctionnel, testé en intégration.

## Lot 4 — Export GitLab/GitHub Pages (page unique)

- Validation de la structure de sortie (chemins relatifs, point d'entrée) conforme aux deux plateformes.
- **Exigences couvertes** : REQ-008.
- **Sortie** : un test d'intégration qui valide la structure produite contre les conventions des deux plateformes (sans déploiement réel — hors périmètre SRS).

## Lot 5 — Export PDF page unique (F2)

- `render/pdf_renderer.py` : intégration de `markdown-pdf`, CSS utilisateur (REQ-010), TOC/bookmarks (REQ-011), sans dépendance système lourde (REQ-009).
- **Exigences couvertes** : REQ-009, REQ-010, REQ-011.
- **Sortie** : CLI `scribpy export pdf input.md --css style.css --output rapport.pdf` fonctionnel.

## Lot 6 — Arborescence et navigation (socle F3/F4)

- `tree/scanner.py` : répertoire de `.md` → `NavNode` racine.
- `tree/nav_model.py` : structure récursive unique (pas de sous-classes, cf. Conception).
- Règle d'ordre par défaut (alphabétique) — hypothèse SRS section 4 à confirmer avec l'utilisateur avant ce lot.
- **Sortie** : `scan(root: Path) -> NavNode` testé isolément, sans dépendance aux renderers.

## Lot 7 — Site HTML multi-pages (F3)

- `render/html_site_renderer.py` : parcours du `NavNode`, génération de la navigation, réutilisation de `html_renderer` par page.
- CSS commun à toutes les pages (REQ-013), export Pages multi-pages (REQ-014, réutilise la validation du lot 4).
- **Exigences couvertes** : REQ-012, REQ-013, REQ-014.
- **Sortie** : CLI `scribpy export site ./docs --css style.css --output dist/` fonctionnel.

## Lot 8 — PDF agrégé depuis arborescence (F4)

- `render/pdf_tree_renderer.py` : parcours du `NavNode`, concaténation via l'API `Section` de `markdown-pdf`, sommaire global.
- **Exigences couvertes** : REQ-015.
- **Sortie** : CLI `scribpy export pdf-tree ./docs --output manuel.pdf` fonctionnel.

## Lot 9 — Durcissement non-fonctionnel transverse

- Revue REQ-016 à REQ-023 sur l'ensemble du périmètre livré (et non lot par lot) : compatibilité Python 3.13, comportement sous proxy SSL d'entreprise (test manuel en environnement réel, non automatisable en CI publique), sécurité (absence d'`eval`/`exec`).
- Documentation utilisateur (README, prérequis Java pour PlantUML — cf. ADR-001).
- **Sortie** : checklist SRS section 3 entièrement vérifiée et tracée.

## Jalons de décision (points de validation avec Antoine avant de poursuivre)

- **Avant Lot 2** : confirmer si `httpx` (dépendance du mode web) doit être un extra `pip` optionnel (`scribpy[web]`) ou une dépendance ferme du package — non tranché dans la conception actuelle.
- **Avant Lot 6** : confirmer la convention de structuration de l'arborescence (fichier d'index, ordre explicite vs alphabétique) — hypothèse SRS section 4.
- **Avant Lot 9 / publication PyPI** : confirmer si le prérequis Java (PlantUML hors-ligne) est acceptable comme contrainte documentée pour les futurs utilisateurs du package, ou si une alternative pip-only doit être recherchée pour ce mode (ADR-002, conséquence négative).
