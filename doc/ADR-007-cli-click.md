# ADR-007 — Exposer l’API publique avec un CLI Click

## Context

Scribpy expose ses workflows par une API Python publique, mais ne fournit pas
de point d’entrée en ligne de commande. Les utilisateurs doivent pouvoir créer,
contrôler, assembler et exporter un projet sans écrire de script Python.

## Decision

Ajouter un adaptateur CLI fondé sur Click et le publier avec le point d’entrée
`scribpy = "scribpy.cli:cli"`. Les sept commandes `new`, `scaffold`,
`validate`, `diagnose`, `build`, `html` et `mkdocs-export` appellent uniquement
les objets et fonctions exposés par `scribpy`, sans reproduire de règle métier.
Les erreurs documentées de l’API sont traduites en erreurs Click de code 1.

## Consequences

- Click devient une dépendance d’exécution directe.
- L’installation du package fournit la commande `scribpy`.
- Le CLI reste testable comme adaptateur isolé avec `CliRunner`.
- `concatenate` est réexportée par le package public pour préserver la
  frontière entre le CLI et les modules internes.

## Alternatives rejected

| Alternative | Raison du rejet |
|---|---|
| `argparse` | Les sous-commandes demandent davantage de code pour ce CLI à sept commandes. |
| Typer | Il ajoute une couche au-dessus de Click sans bénéfice net pour ces signatures simples. |
