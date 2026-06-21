---
type: adr
status: accepted
date: 2026-06-21
tags: [architecture, adr, scribpy, diagrammes]
---

# ADR-002 : Offrir un double mode de rendu des diagrammes (web et hors-ligne), réglable globalement

## Statut

Accepté — remplace ADR-001.

## Contexte

ADR-001 retenait un rendu exclusivement hors-ligne pour PlantUML et Mermaid, justifié par les contraintes réseau de l'environnement Windows contraint d'Antoine (proxy avec interception SSL, REQ-016/REQ-017) et par sa pratique déjà établie (rendu local pour Obsidian/PlantUML).

Cette décision a été révisée : l'usage de Scribpy n'est pas circonscrit au seul poste contraint d'Antoine — un mode web (services officiels PlantUML public et `mermaid.ink`) est désormais explicitement demandé en complément du mode hors-ligne, avec un réglage applicable par l'utilisateur. Le mode hors-ligne reste nécessaire pour les contextes où l'accès réseau est restreint ; le mode web simplifie l'usage dans les contextes où l'accès web est disponible (pas de prérequis Java, pas de package `mmdc` à installer).

La question du comportement en cas d'échec du mode web (proxy bloquant, service indisponible) devait être tranchée explicitement : un repli automatique vers le mode hors-ligne masquerait un problème réseau par un changement de comportement non demandé par l'utilisateur au moment de l'exécution.

## Décision

Scribpy expose un réglage unique (`RenderMode.WEB` / `RenderMode.OFFLINE`) appliqué globalement à l'ensemble du document pour les deux moteurs de diagramme (PlantUML et Mermaid). En mode web, Scribpy appelle le serveur PlantUML public et `mermaid.ink` selon le moteur ; en mode hors-ligne, Scribpy utilise respectivement le `.jar` PlantUML local (subprocess) et `mmdc` (rendu Python pur). En cas d'échec d'un appel en mode web, Scribpy lève une erreur explicite nommant le bloc et le mode actif, sans basculer automatiquement vers le mode hors-ligne.

## Conséquences

- \+ Usage simplifié pour les utilisateurs disposant d'un accès web non restreint : aucun prérequis Java ni package `mmdc` à installer pour découvrir ou utiliser Scribpy rapidement.
- \+ Le mode hors-ligne reste disponible et inchangé pour l'environnement contraint d'Antoine — aucune régression sur le cas d'usage initial.
- \+ Le comportement fail-fast en mode web (REQ-025) rend les échecs réseau visibles immédiatement, évitant qu'un document produit silencieusement avec un mode différent de celui demandé induise en erreur sur la disponibilité réelle du réseau.
- \+ Le réglage global unique (plutôt que par moteur ou par bloc) garde la configuration simple à exposer en CLI et à documenter, conforme à la demande explicite de granularité.
- – Le mode web introduit une dépendance fonctionnelle à deux domaines publics externes (service PlantUML, `mermaid.ink`) non maîtrisés par Antoine ni par Anthropic-side du projet : disponibilité, limites de débit, et évolution de leur API échappent au contrôle du package — à documenter comme risque d'usage du mode web, pas du mode hors-ligne.
- – Une dépendance supplémentaire (`httpx`) est introduite uniquement pour le mode web ; son usage reste nul si l'utilisateur n'active jamais ce mode, ce qui pose la question (non tranchée ici) de l'isoler en extra `pip` pour ne pas l'imposer aux utilisateurs strictement hors-ligne.
- – Dans l'environnement contraint d'Antoine spécifiquement, le mode web ne fonctionnera pas tant que les domaines du service PlantUML public et de `mermaid.ink` ne sont pas explicitement autorisés par le proxy d'entreprise — Scribpy ne tente aucun contournement réseau (pas de gestion de certificat alternatif intégrée), cette autorisation reste hors du périmètre du package.
- – Deux implémentations supplémentaires à maintenir et tester (`plantuml_web`, `mermaid_web`) en plus des deux existantes, ce qui double la surface de code du sous-système de rendu de diagrammes par rapport à ADR-001.
