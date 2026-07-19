# ADR-003 — Export HTML avec burger menu

## Context

scribpy assemble des collections Markdown en un seul fichier `.md`.
Des utilisateurs ont besoin d'un rendu HTML portable avec navigation,
sans dépendre d'un outil externe (MkDocs, Pandoc).

La TOC Markdown auto-générée par `generate_toc()` est bien positionnée
dans le flux assemblé mais inadaptée à la navigation HTML : elle pollue
le corps du document et ne bénéficie d'aucune interactivité.

## Decision

Créer `src/scribpy/core/html/` comme module standalone exposant une
unique fonction publique `html_export(source, output, toc_depth, css)`.

Le module est divisé en quatre responsabilités indépendantes :

| Module | Responsabilité unique |
|---|---|
| `toc_extractor.py` | Extraire les headings et retirer le bloc TOC du Markdown |
| `converter.py` | Convertir Markdown → HTML (adaptateur `python-markdown`) |
| `page_builder.py` | Assembler le template HTML complet (f-string, zéro dépendance template) |
| `__init__.py` | Orchestrer le flux et exposer `html_export()` |

Les assets statiques (`default.css`, `burger.js`) sont embarqués dans
`src/scribpy/core/html/assets/` et lus via `importlib.resources`.
Le HTML produit est autonome (pas de ressources externes).

Le paramètre `toc_depth` est transmis depuis `BuildSettings.toc_depth`
du manifest — le manifest n'est pas relu par le module HTML.

## Consequences

- `python-markdown` (PyPI : `Markdown>=3.6`) devient une nouvelle
  dépendance directe.
- Le HTML produit est entièrement autonome (offline-ready).
- La TOC Markdown dans le `.md` source reste intacte ; seul le HTML
  la masque et la convertit en burger menu.
- Le module n'a aucune dépendance sur `assembly/` : il opère sur un
  `.md` déjà écrit sur disque.

## Alternatives rejected

| Alternative | Raison du rejet |
|---|---|
| Jinja2 comme moteur de template | Surpoids pour un template unique et fixe |
| `mistune` | Moins mature pour les extensions tables/fenced-code/footnotes |
| Pandoc via subprocess | Dépendance système hors contrôle de `pyproject.toml` |
| Exposer un flag `--format html` dans un CLI | Pas de CLI existant ; reporter la décision CLI à un ADR dédié |
