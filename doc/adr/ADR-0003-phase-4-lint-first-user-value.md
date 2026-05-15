# ADR-0003 — Planification de la phase 4 : lint-first user value

**Date:** 2026-05-15  
**Statut:** propose  
**Decideurs:** Antoine Barre  
**References:** `doc/FUNCTIONAL_CHAINS.md`, `doc/SDD.md`, `doc/adr/ADR-0002-phase-3-parse-extract-document-semantics.md`

---

## Contexte

`doc/FUNCTIONAL_CHAINS.md` definit la phase 4 comme la chaine fonctionnelle
FC-04 Lint Documentation Quality.

Les phases 2 et 3 rendent deja Scribpy capable de :

1. charger un projet et sa configuration ;
2. decouvrir les sources Markdown et construire un `DocumentIndex` deterministe ;
3. parser les documents ;
4. extraire les titres, liens et assets sous forme de donnees semantiques typees.

La phase 4 doit transformer ce modele semantique en valeur utilisateur directe :
detecter des defauts de documentation avant qu'une chaine de build complete
n'existe.

Dans `doc/FUNCTIONAL_CHAINS.md`, FC-04 couvre :

```text
Project + Document[] + DocumentIndex + Registry
  -> select_lint_rules
  -> run_lint_rules
  -> aggregate diagnostics
  -> should_fail_build
  -> LintResult
```

Cette phase est volontairement centree sur la qualite documentaire. Elle ne
produit pas encore d'artefact de build, ne transforme pas les documents et ne
rend pas de sortie Markdown, HTML ou PDF. Son role est de stabiliser les regles,
les diagnostics et le point d'extension qui seront reutilises par les phases
suivantes.

---

## Decision

La phase 4 sera implementee comme une tranche verticale complete :

```text
CLI -> parse project documents -> lint context -> rule registry -> diagnostics -> exit code
```

Le livrable principal sera une capacite utilisateur observable :

```text
scribpy lint
```

Cette commande devra :

- charger le projet et parser les documents via la chaine deja disponible ;
- construire un contexte de lint partage entre les regles ;
- selectionner les regles actives depuis un registre extensible ;
- executer au minimum les regles `LINT001` a `LINT004` ;
- agreger des diagnostics stables avec severite, code, chemin, ligne et hint ;
- calculer `LintResult.failed` selon une politique explicite ;
- retourner un code de sortie coherent avec les commandes deja presentes.

La phase 4 introduira un `ExtensionRegistry` minimal pour les regles de lint,
mais pas encore un systeme de plugins complet. Le registre devra permettre aux
regles natives et futures regles externes de partager le meme contrat sans
coupler le coeur applicatif a leur implementation concrete.

La politique de defaillance sera simple pour cette phase :

- toute erreur (`severity="error"`) rend `LintResult.failed = True` ;
- les warnings n'echouent pas la commande par defaut ;
- la configuration fine du seuil de severite pourra etre ajoutee plus tard si
  le besoin devient reel.

---

## Perimetre Fonctionnel

### Inclus

- `scribpy.lint`
  - `LintContext` contenant au minimum `project`, `documents`, `document_index`
    et les utilitaires de resolution utiles aux regles ;
  - protocole ou contrat `LintRule` ;
  - execution ordonnee des regles ;
  - aggregation des diagnostics ;
  - calcul du `LintResult`.

- `scribpy.extensions`
  - `ExtensionRegistry` minimal pour enregistrer et recuperer les regles de lint ;
  - chargement des regles natives par defaut ;
  - API stable assez petite pour etre durcie en phase 9.

- Regles natives MVP
  - `LINT001` : document sans titre H1 ;
  - `LINT002` : hierarchie de titres incoherente ;
  - `LINT003` : lien interne casse ;
  - `LINT004` : image ou asset local reference mais introuvable.

- `scribpy.core`
  - service applicatif `lint_project(...) -> LintResult` ou equivalent ;
  - reutilisation de la chaine de chargement/parsing existante plutot qu'une
    seconde implementation divergente ;
  - restitution au lint du contexte necessaire a la resolution locale
    (`root`, `source_dir`, `documents`, `document_index`).

- `scribpy.cli`
  - commande `scribpy lint` ;
  - option `--root` coherente avec `index check` et `parse check` ;
  - affichage des diagnostics ;
  - codes de sortie `0`, `1`, `2`.

- Tests
  - regles unitaires ;
  - resolution de liens entre documents ;
  - validation d'assets ;
  - integration du registre ;
  - service applicatif ;
  - comportement CLI.

### Exclus

- transformations de contenu ;
- generation d'un artefact Markdown assemble ;
- builders HTML ou PDF ;
- rendu de diagrammes ;
- plugins dynamiques charges depuis l'exterieur ;
- configuration avancee de severite ou de profils de lint ;
- autofix ou reecriture des sources.

---

## Etat Actuel

Deja disponible :

- `Document`, `Heading`, `Reference`, `AssetRef`, `DocumentIndex`, `Project` ;
- `Diagnostic` et `LintResult` ;
- `parse_project_documents(...)` comme point d'entree applicatif FC-03 ;
- extraction des titres, liens et assets ;
- commandes CLI `scribpy index check` et `scribpy parse check` ;
- paquet `scribpy.lint` present mais encore vide ;
- paquet `scribpy.extensions` present mais encore vide.

A creer ou completer :

- contrats `LintContext` et `LintRule` ;
- `ExtensionRegistry` minimal ;
- implementation des regles `LINT001` a `LINT004` ;
- logique de resolution des liens et assets locaux ;
- service `lint_project` ;
- commande CLI `scribpy lint` ;
- couverture de tests associee.

---

## Regles MVP

| Code | Regle | Detection attendue |
|---|---|---|
| `LINT001` | Missing H1 | aucun titre de niveau 1 dans un document |
| `LINT002` | Heading hierarchy | saut de niveau non autorise, par exemple `#` puis `###` |
| `LINT003` | Broken internal link | cible locale absente ou ancre cible introuvable |
| `LINT004` | Missing local asset | image ou asset local reference mais fichier absent |

Principes communs :

- les liens externes (`http`, `https`, `mailto`, etc.) ne sont pas verifies dans
  cette phase ;
- les ancres locales `#section` sont resolues contre le document courant ;
- les liens relatifs vers un autre document sont resolus depuis le document
  source, puis normalises contre l'index connu ;
- la resolution des cibles locales est centralisee dans un helper partage par
  `LINT003` et `LINT004` afin d'eviter deux interpretations concurrentes des
  chemins ;
- les diagnostics doivent pointer autant que possible la ligne extraite durant
  la phase 3 ;
- les regles restent pures : elles lisent le contexte et retournent des
  diagnostics sans modifier les documents.

---

## Plan de Realisation

### Etape 1 — Contrats de lint

Objectif : definir les interfaces stables de la phase.

A faire :

- creer `LintContext` avec les produits de donnees necessaires aux regles ;
- definir un contrat `LintRule` avec un identifiant stable et une methode
  d'execution retournant `tuple[Diagnostic, ...]` ;
- definir une fonction d'execution commune qui applique les regles dans un ordre
  deterministe ;
- conserver `LintResult` comme resultat applicatif unique.

### Etape 2 — Registre d'extensions minimal

Objectif : decoupler la selection des regles de leur implementation.

A faire :

- creer `ExtensionRegistry` dans `scribpy.extensions` ;
- permettre l'enregistrement et la recuperation de regles de lint ;
- fournir un constructeur ou helper chargeant les regles natives ;
- conserver une API volontairement petite, sans decouverte dynamique de plugins
  a ce stade.

### Etape 3 — Regles structurelles

Objectif : valider les titres extraits par la phase 3.

A faire :

- implementer `LINT001` pour signaler les documents sans H1 ;
- implementer `LINT002` pour detecter les sauts de niveau de titres ;
- reutiliser les lignes deja presentes sur `Heading` ;
- definir des messages et hints stables.

### Etape 4 — Resolution de liens et assets

Objectif : exploiter les `Reference` et `AssetRef` deja extraits.

A faire :

- construire des helpers de resolution pour distinguer :
  - URL externes ;
  - ancre locale ;
  - chemin relatif vers un document ;
  - chemin relatif vers un asset ;
- implementer `LINT003` :
  - document cible inexistant ;
  - ancre inexistante dans le document cible ;
- implementer `LINT004` :
  - asset local introuvable ;
- garder la logique de resolution mutualisee pour eviter des divergences entre
  lint et futures phases de transformation.

### Etape 5 — Service applicatif

Objectif : exposer une operation reutilisable par le CLI et les futurs builders.

A faire :

- implementer `lint_project(root, filesystem=None, parser=None, registry=None)` ;
- reutiliser la meme chaine de chargement/parsing que `parse_project_documents`
  pour obtenir les documents sans dupliquer les decisions de phase 2 et 3 ;
- reconstruire ou transporter explicitement les produits de contexte utiles au
  lint (`root`, `source_dir`, `document_index`) ;
- si le parsing echoue, propager les diagnostics existants et ne pas executer les
  regles de contenu sur un ensemble incomplet ;
- construire `LintContext` ;
- executer les regles selectionnees ;
- agreger les diagnostics de parsing et de lint ;
- calculer `failed` via la politique de severite retenue.

### Etape 6 — CLI `scribpy lint`

Objectif : livrer la capacite utilisateur de la phase 4.

A faire :

- ajouter la commande `lint` a `scribpy.cli.main` ;
- accepter `--root` avec la meme semantique que les commandes existantes ;
- imprimer les diagnostics sur `stderr` ;
- retourner :
  - `0` sans diagnostic bloquant ;
  - `1` si `LintResult.failed` vaut `True` ;
  - `2` pour une erreur de syntaxe CLI ;
- documenter dans l'aide ce qui est verifie.

### Etape 7 — Tests et qualite

Objectif : verrouiller les contrats avant la phase 5.

A faire :

- tests unitaires pour chaque regle ;
- tests de resolution d'ancres intra-document et inter-documents ;
- tests d'assets manquants ;
- tests du registre natif ;
- tests d'integration sur `lint_project` ;
- tests CLI sur les codes de sortie et l'affichage des diagnostics ;
- executer `make check` avant cloture de la phase.

---

## Diagnostics attendus

| Code | Severite par defaut | Cas |
|---|---|---|
| `LINT001` | error | document sans H1 |
| `LINT002` | error | hierarchie de titres incoherente |
| `LINT003` | error | lien interne casse ou ancre cible absente |
| `LINT004` | error | asset local introuvable |

Les diagnostics des phases precedentes (`CFG*`, `PRJ*`, `IDX*`, `PRS*`) restent
valides et peuvent remonter dans `scribpy lint` si le projet ne peut pas etre
charge ou parse correctement.

---

## Consequences

### Positives

- la phase 4 fournit une vraie valeur Docs-as-Code avant tout builder ;
- elle valide que le modele semantique produit en phase 3 est suffisamment riche ;
- elle introduit un premier point d'extension sans prematurement construire tout
  le systeme de plugins ;
- elle prepare la phase 5, ou les builds pourront echouer proprement sur les
  diagnostics de lint.

### Trade-offs acceptes

- le registre est volontairement minimal et pourra evoluer en phase 9 ;
- les liens externes ne sont pas verifies a ce stade ;
- la politique de severite reste simple pour eviter de figer trop tot un modele
  de configuration ;
- `scribpy lint` depend de la chaine de parsing complete, ce qui est desirable
  pour la coherence mais signifie qu'un echec de parsing bloque les regles aval.

---

## Criteres de Sortie

La phase 4 est consideree terminee lorsque :

1. `scribpy lint` fonctionne sur un projet valide et sur un projet invalide ;
2. `LINT001` a `LINT004` emettent des diagnostics stables et testes ;
3. les liens casses et images manquantes sont detectes ;
4. le registre de lint permet d'enregistrer et d'executer les regles natives ;
5. `LintResult.failed` et les codes de sortie CLI respectent la politique
   decidee ;
6. la suite de tests et `make check` passent.

---

## Decisions differees

Les sujets suivants sont explicitement repousses :

- profils de lint et activation/desactivation fine par configuration ;
- seuil de severite configurable (`warn-as-error`, profils CI, etc.) ;
- verification reseau des liens externes ;
- autofix ;
- chargement dynamique de plugins externes ;
- integration du lint dans les builders, qui sera traitee lors de la phase 5.
