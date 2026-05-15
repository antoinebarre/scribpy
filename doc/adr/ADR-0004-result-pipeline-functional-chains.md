# ADR-0004 — Result Pipeline pour les chaines fonctionnelles

**Date:** 2026-05-15  
**Statut:** propose  
**Decideurs:** Antoine Barre  
**References:** `doc/FUNCTIONAL_CHAINS.md`, `doc/adr/ADR-0002-phase-3-parse-extract-document-semantics.md`, `doc/adr/ADR-0003-phase-4-lint-first-user-value.md`

---

## Contexte

Scribpy est structure autour de chaines fonctionnelles :

```text
configure -> scan -> parse -> extract -> lint -> transform -> assemble -> build
```

Les phases 3 et 4 ont introduit deux services applicatifs :

- `parse_project_documents` ;
- `lint_project`.

Ces services partagent deja le meme tronc :

```text
resolve config -> load config -> scan sources -> build index -> parse documents
```

Mais ce tronc est encore orchestre localement dans plusieurs fonctions avec des
sorties anticipees repetitives. Cela cree trois problemes :

1. la logique commune risque de diverger entre les chaines ;
2. les services applicatifs concentrent trop de controle de flux ;
3. les futures phases de build devront soit dupliquer cette orchestration, soit
   la refactorer plus tard sous pression.

La phase 5 va ajouter une nouvelle chaine qui reutilisera exactement ce meme
tronc. Il est donc pertinent de formaliser maintenant le pattern interne de
composition des chaines.

---

## Decision

Les chaines fonctionnelles internes seront composees via un pattern
**Result Pipeline** :

```text
PipelineResult[State]
  -> bind(step)
  -> bind(step)
  -> bind(step)
  -> value | diagnostics
```

Chaque etape :

- recoit un etat immuable ;
- retourne un `PipelineResult` contenant :
  - la nouvelle valeur ;
  - les diagnostics produits par l'etape ;
  - un indicateur d'echec ;
- ne connait pas les services applicatifs aval.

Le pipeline :

- accumule les diagnostics dans l'ordre d'execution ;
- court-circuite automatiquement les etapes suivantes apres un echec ;
- conserve la valeur produite lorsqu'elle reste utile a l'appelant, par exemple
  les documents deja parses avant une erreur partielle ;
- laisse les APIs publiques (`parse_project_documents`, `lint_project`, futurs
  builders) exposees sous forme de facades simples.

Le tronc projet commun sera represente par un etat interne dedie :

```text
ProjectPipelineState
```

et par des etapes communes :

1. resolution de configuration ;
2. chargement de configuration ;
3. scan des sources ;
4. construction de l'index ;
5. parsing des documents.

---

## Motivation

Ce pattern correspond mieux a l'architecture fonctionnelle documentee de
Scribpy qu'une orchestration imperative dupliquee.

Il permet de rendre visibles dans le code les produits intermediaires deja
presentes dans `FUNCTIONAL_CHAINS.md` :

```text
Config -> SourceFile[] -> DocumentIndex -> Document[]
```

Le choix d'un `Result Pipeline` est prefere a :

- **Chain of Responsibility**, car les etapes ne sont pas interchangeables et
  doivent toutes s'executer dans un ordre fixe ;
- **Template Method**, car il introduirait prematurement une hierarchie de
  classes pour des workflows encore simples ;
- **state machine**, car les transitions actuelles restent lineaires.

---

## Perimetre

### Inclus

- `PipelineResult[T]`
  - `ok(...)` ;
  - `fail(...)` ;
  - `bind(...)`.

- `ProjectPipelineState`
  - chemin de depart ;
  - services injectes ;
  - configuration ;
  - racine projet ;
  - fichiers sources ;
  - index ;
  - fichiers ordonnes ;
  - documents parses.

- etapes communes du pipeline projet ;
- reutilisation du pipeline par :
  - `parse_project_documents` ;
  - la preparation de `lint_project`.

### Exclus

- DSL de pipeline ;
- graphe dynamique d'etapes ;
- moteur de plugins ;
- parallelisation ;
- refonte de `run_index_check`, qui peut rester autonome tant que son perimetre
  est plus court ;
- pipeline de build complet, qui sera introduit lors de la phase 5.

---

## Consequences

### Positives

- tronc commun explicite et reutilisable ;
- baisse de la complexite dans les services applicatifs ;
- propagation uniforme des diagnostics ;
- preparation naturelle des phases 5+ ;
- tests possibles a deux niveaux :
  - etapes unitaires ;
  - chaines applicatives.

### Trade-offs acceptes

- un type generique supplementaire dans `core` ;
- un etat interne un peu plus riche que les besoins immediats de chaque service ;
- une convention supplementaire a respecter pour les futures etapes.

Ces couts sont juges inferieurs a la duplication qui apparaitrait avec trois ou
quatre chaines applicatives independantes.

---

## Regles de conception

1. Les etapes restent petites et sans effet de bord autre que ceux necessaires a
   leur fonction.
2. Les APIs publiques ne retournent pas `PipelineResult` ; elles conservent leurs
   types metier (`ParseResult`, `LintResult`, futurs `BuildResult`).
3. Le pipeline reste interne et minimaliste : pas de framework maison.
4. Les diagnostics utilisateur restent portes par les types metier existants.
5. Les nouvelles chaines doivent reutiliser le tronc commun lorsqu'elles
   consomment les memes produits intermediaires.

---

## Impact attendu

Apres adoption :

- `parse_project_documents` devient une facade autour du pipeline projet ;
- `lint_project` reutilise le meme pipeline puis ajoute sa propre etape de lint ;
- la phase 5 pourra enchainer `lint -> assemble markdown -> build artifact`
  sans recopier la preparation projet.

---

## Criteres d'acceptation

La decision est consideree appliquee lorsque :

1. `PipelineResult` et `ProjectPipelineState` existent ;
2. `parse_project_documents` et `lint_project` reutilisent le tronc commun ;
3. les diagnostics et comportements observables restent inchanges ;
4. la complexite des facades applicatives diminue ;
5. `make check` passe avec 100% de couverture.
