# ADR-006 — Garder Kroki par défaut et proposer Mermaid CLI

## Context

Contrairement à PlantUML, Mermaid ne fournit pas de service PNG officiel
public. Le projet Mermaid maintient `@mermaid-js/mermaid-cli`, dont la commande
`mmdc` produit des images statiques, mais ce CLI ne fonctionne pas de manière
fiable dans tous les environnements ciblés. Kroki reste dans ce contexte le
choix par défaut le plus opérationnel, tandis que le CLI doit rester disponible
comme stratégie locale optionnelle.

## Decision

Ajouter `MermaidCliRenderer` comme backend optionnel sous le nom
`mermaid_cli`. Kroki reste le backend par défaut pour sa fiabilité observée
dans ce projet. Le renderer CLI résout l'exécutable avec `shutil.which`,
écrit la source dans un dossier temporaire isolé, appelle `mmdc` avec une
liste d'arguments sans shell, lit le PNG puis supprime le dossier temporaire.

Le champ `build.mermaid_command` vaut `mmdc` par défaut. Il permet de cibler
une installation particulière sans intégrer Node, Chromium ou Mermaid CLI aux
dépendances Python de Scribpy.

Les backends disponibles sont :

- `kroki`, valeur par défaut ;
- `mermaid_cli`, rendu local optionnel ;
- `local`, alias rétrocompatible de `mermaid_cli` ;
- `web`, alias rétrocompatible de `kroki`.

`render_diagram_blocks()` reste l'unique point d'entrée du merge et de
l'export MkDocs. Il transmet `BuildSettings.mermaid_command` à la factory.

## Consequences

- Le rendu Mermaid par défaut continue d'utiliser Kroki.
- L'utilisateur doit installer Node.js, Chromium/Puppeteer et
  `@mermaid-js/mermaid-cli` uniquement pour demander le backend CLI.
- Une commande absente, un timeout, un code retour non nul ou un PNG manquant
  produit un `MermaidRenderError` explicite.
- `web` reste disponible comme alias rétrocompatible de Kroki.
- Aucune dépendance Python n'est ajoutée.

## Alternatives rejected

| Alternative | Raison du rejet |
|---|---|
| Rendre Mermaid CLI obligatoire | Le CLI ne fonctionne pas de manière fiable dans tous les environnements ciblés |
| Utiliser Mermaid Live Editor comme service PNG | Ce n'est pas une API officielle de rendu PNG |
| Embarquer Node et Chromium avec Scribpy | Hors du gestionnaire de dépendances Python et trop lourd |
| Exécuter `npx` automatiquement | Peut télécharger et exécuter du code au moment du build |
| Utiliser `shell=True` | Introduit un risque d'injection de commande inutile |
