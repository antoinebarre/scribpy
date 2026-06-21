---
type: adr
status: accepted
date: 2026-06-21
tags: [architecture, adr, scribpy, diagrammes]
---

# ADR-001 : Rendre les diagrammes PlantUML et Mermaid localement, sans Node.js ni navigateur complet

## Statut

Remplacé par ADR-002 — décision révisée suite à une demande explicite de double mode (web et hors-ligne) réglable par l'utilisateur, plutôt que le seul mode hors-ligne initialement retenu ici.

## Contexte

Scribpy doit transformer des blocs PlantUML et Mermaid présents dans du Markdown en diagrammes intégrés à la sortie HTML ou PDF (REQ-005, REQ-006). Le poste de travail cible est Windows, sans droits administrateur, derrière un proxy d'entreprise avec interception SSL (REQ-016, REQ-017). L'installation doit rester possible via `pip`/`uv` seul, sans étape d'installation système.

L'écosystème Mermaid repose historiquement sur `mermaid-cli` (Node.js + npm + Mermaid CLI) ou sur des wrappers Python (`mermaid-py`, `mermaid_cli` Python) qui, par défaut, délèguent le rendu soit à un service web public (`mermaid.ink`), soit à un navigateur headless (Chromium/Playwright) téléchargé séparément. Aucune de ces deux voies n'est directement compatible avec l'environnement cible : la première suppose un accès réseau sortant non maîtrisé vers un service tiers, la seconde suppose le téléchargement et la gestion d'un binaire navigateur hors du périmètre `pip`/`uv`.

Pour PlantUML, Antoine dispose déjà d'un usage établi (intégration Obsidian) reposant sur un `.jar` local exécuté via Java, en évitant explicitement le serveur PlantUML public pour des raisons de confidentialité.

## Décision

Scribpy rend les diagrammes Mermaid via le package pip `mmdc` (rendu Python natif, sans Node.js ni navigateur, basé sur PhantomJS via `phasma`), et rend les diagrammes PlantUML via un wrapper `subprocess` appelant un `.jar` PlantUML fourni/configuré par l'utilisateur, cohérent avec l'usage déjà en place pour Obsidian.

## Conséquences

- \+ Aucune dépendance à un service web public pour le rendu de diagrammes : conforme à REQ-017 et à la pratique de confidentialité déjà adoptée par Antoine.
- \+ Installation entièrement gérable via `uv add` sans étape d'installation système ni droits administrateur (REQ-016).
- \+ Cohérence d'outillage avec le flux Obsidian/PlantUML existant (même `.jar`, même logique d'exécution locale).
- \+ Le dispatch PlantUML/Mermaid via `Protocol` + dictionnaire de callables (cf. document de conception) permet d'ajouter un futur moteur de rendu sans toucher au code existant.
- – Dépendance à un package tiers (`mmdc`) récent et peu éprouvé en production à la date de cette décision ; sa maintenance à moyen terme n'est pas garantie — à surveiller, avec `mermaid-cli` (Node.js) comme repli documenté si `mmdc` devient inutilisable.
- – Le rendu PlantUML suppose la présence de Java sur le poste (déjà vrai pour Antoine via Obsidian, mais ce n'est pas une garantie pour tout futur utilisateur du package publié sur PyPI) — à documenter explicitement comme prérequis dans le README de Scribpy, pas comme dépendance pip.
- – Deux mécanismes de rendu différents (subprocess Java vs lib Python pure) à maintenir et tester séparément, plutôt qu'un seul moteur unifié — accepté car aucune solution unique ne couvre les deux langages de diagramme dans l'environnement contraint actuel.
