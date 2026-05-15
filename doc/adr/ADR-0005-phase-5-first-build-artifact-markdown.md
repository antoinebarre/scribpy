# ADR-0005 — Planification de la phase 5 : premier artefact de build Markdown

**Date:** 2026-05-15  
**Statut:** propose  
**Decideurs:** Antoine Barre  
**References:** `doc/FUNCTIONAL_CHAINS.md`, `doc/SDD.md`, `doc/adr/ADR-0003-phase-4-lint-first-user-value.md`, `doc/adr/ADR-0004-result-pipeline-functional-chains.md`

---

## Contexte

`doc/FUNCTIONAL_CHAINS.md` definit la phase 5 comme le premier livrable de
build visible par l'utilisateur : produire un document Markdown assemble a
partir d'un projet Scribpy valide.

Les phases precedentes rendent deja Scribpy capable de :

1. charger un projet et sa configuration ;
2. decouvrir les sources Markdown et construire un `DocumentIndex`
   deterministe ;
3. parser les documents et extraire leur semantique ;
4. executer les regles de lint natives ;
5. reutiliser le tronc commun via le `Result Pipeline` interne.

La prochaine capacite utile n'est donc pas encore le rendu HTML/PDF ni une
pipeline de transformation riche. Il faut d'abord fermer la premiere chaine de
build complete avec l'artefact le moins risque : un Markdown assemble.

Dans `doc/FUNCTIONAL_CHAINS.md`, la phase 5 couvre principalement FC-06 :

```text
DocumentIndex + TransformedDocument[]
  -> order_documents
  -> merge_documents
  -> normalize_boundaries
  -> write build/markdown/document.md
```

La feuille de route place FC-05 Transform Document Set en phase 6. La phase 5
doit donc introduire uniquement le contrat minimal permettant de conserver cette
frontiere future, sans anticiper la generation de TOC, la numerotation de
sections ou la reecriture de liens.

---

## Decision

La phase 5 sera implementee comme une tranche verticale complete :

```text
CLI -> project parse pipeline -> lint -> minimal transform boundary -> assemble -> write artifact
```

Le livrable principal sera une capacite utilisateur observable :

```text
scribpy build markdown
```

Cette commande devra :

- reutiliser le pipeline projet partage pour charger, indexer et parser les
  documents ;
- executer le lint avant toute ecriture d'artefact ;
- interrompre le build lorsqu'un diagnostic d'erreur est present ;
- ordonner les documents selon le `DocumentIndex` deja calcule ;
- assembler leur contenu de maniere deterministe ;
- normaliser les separations entre documents sans modifier les sources ;
- ecrire un artefact Markdown a un chemin de sortie stable ;
- retourner un `BuildResult` contenant les diagnostics et les artefacts produits.

La phase 5 introduira un **protocole de transformation minimal** comme jointure
architecturale entre le parsing et l'assemblage, mais le comportement par defaut
sera volontairement identitaire : les documents transmis au builder conservent
leur contenu source. Les transformations fonctionnelles visibles resteront hors
perimetre jusqu'a la phase 6.

Le chemin de sortie MVP sera :

```text
build/markdown/document.md
```

et le builder Markdown devra produire un seul `BuildArtifact` avec :

- `target="markdown"` ;
- `artifact_type="document"` ;
- `path` pointant vers le fichier assemble.

---

## Perimetre Fonctionnel

### Inclus

- `scribpy.transforms`
  - contrat minimal pour une transformation ou une etape de transformation ;
  - contexte/resultat minimal si necessaire pour conserver une API compatible
    avec FC-05 ;
  - transformation identitaire native par defaut.

- `scribpy.builders`
  - type interne representant le document assemble, si utile pour isoler le
    builder des documents sources ;
  - assemblage Markdown deterministe ;
  - normalisation des frontieres entre documents ;
  - ecriture de `build/markdown/document.md` ;
  - creation du `BuildArtifact` correspondant.

- `scribpy.core`
  - facade `merge_documents(...)` pour l'assemblage pur ;
  - facade `build_project(...) -> BuildResult` pour la cible Markdown ;
  - reutilisation du pipeline projet defini par l'ADR-0004 ;
  - reutilisation de la logique de lint existante sans divergence de politique.

- `scribpy.cli`
  - commande `scribpy build markdown` ;
  - option `--root` coherente avec `index check`, `parse check` et `lint` ;
  - affichage des diagnostics ;
  - affichage du chemin d'artefact produit en cas de succes ;
  - codes de sortie `0`, `1`, `2` coherents avec le reste du CLI.

- Tests
  - ordre d'assemblage conforme au `DocumentIndex` ;
  - normalisation deterministe des frontieres ;
  - ecriture du chemin de sortie attendu ;
  - aucun artefact ecrit en cas d'erreur de lint ;
  - retour de `BuildResult` ;
  - comportement CLI.

### Exclus

- generation de table des matieres ;
- numerotation de sections ;
- resolution avancee de references croisees ;
- reecriture de liens par cible ;
- registre de transformations complet ;
- builder HTML ;
- builder PDF ;
- copie d'assets et rendu de diagrammes ;
- configuration avancee des sorties de build ;
- build multi-cibles via `scribpy build` sans sous-commande.

---

## Etat Actuel

Deja disponible :

- `Document`, `DocumentIndex`, `BuildArtifact`, `BuildResult` ;
- `parse_project_documents(...)` et `lint_project(...)` ;
- le pipeline projet partage (`PipelineResult`, `ProjectPipelineState`) ;
- les commandes CLI `scribpy index check`, `scribpy parse check` et
  `scribpy lint` ;
- les paquets `scribpy.builders` et `scribpy.transforms`, encore vides ;
- les utilitaires Markdown existants, utiles comme support mais insuffisants
  pour definir a eux seuls le contrat de build.

A creer ou completer :

- le contrat minimal de transformation ;
- le type de document assemble ou equivalent ;
- l'algorithme d'assemblage Markdown ;
- le builder Markdown et l'ecriture d'artefact ;
- le service applicatif de build Markdown ;
- l'integration CLI ;
- les tests unitaires et de chaine associes.

---

## Regles de Build MVP

| Sujet | Regle retenue |
|---|---|
| Ordre | suivre strictement l'ordre du `DocumentIndex` |
| Entree du builder | documents parses deja ordonnes par le pipeline projet |
| Contenu | utiliser le corps source transmis par la chaine, sans mutation des fichiers d'origine |
| Frontieres | produire exactement une separation Markdown stable entre deux documents |
| Sortie | ecrire un seul fichier `build/markdown/document.md` |
| Lint | ne pas ecrire d'artefact si la chaine de preparation ou le lint contient une erreur |
| Resultat | retourner un `BuildResult`, y compris en echec |

Principes communs :

- le builder ne doit pas redecouvrir les fichiers ni recalculer l'ordre ;
- l'assemblage doit etre pur et testable sans acces disque ;
- l'ecriture doit etre isolee du calcul du contenu pour faciliter les futurs
  builders ;
- la phase 5 ne doit pas exposer de comportement de transformation qui sera
  ensuite remplace en phase 6 ;
- les diagnostics utilisateur doivent rester coherents avec les codes et la
  politique de defaillance deja etablis.

---

## Plan de Realisation

### Etape 1 — Frontiere minimale de transformation

Objectif : preparer FC-05 sans l'implementer prematurement.

A faire :

- definir le contrat minimal qu'un futur transform devra respecter ;
- introduire un resultat ou type intermediaire seulement s'il clarifie la
  separation entre documents parses et documents prets pour une cible ;
- fournir une implementation identitaire native ;
- documenter que les transforms visibles restent prevus pour la phase 6.

### Etape 2 — Assemblage pur

Objectif : produire un contenu Markdown assemble sans effet de bord.

A faire :

- definir `merge_documents(...)` ou equivalent ;
- prendre en entree la sequence deja ordonnee ;
- concatener les contenus sans modifier les objets `Document` ;
- normaliser les sauts de ligne entre documents ;
- ajouter des tests couvrant l'ordre, les documents vides et les frontieres deja
  terminees ou non par un saut de ligne.

### Etape 3 — Builder Markdown

Objectif : transformer le contenu assemble en artefact de build.

A faire :

- ecrire le contenu dans `build/markdown/document.md` ;
- creer le repertoire de sortie si necessaire ;
- retourner un `BuildArtifact(target="markdown", artifact_type="document")` ;
- convertir les echecs d'ecriture en diagnostics de build plutot qu'en erreurs
  brutes pour l'utilisateur.

Diagnostics proposes :

- `BLD001` : cible de build inconnue ou non supportee ;
- `BLD002` : build interrompu a cause de diagnostics bloquants en amont ;
- `BLD003` : echec d'ecriture de l'artefact Markdown.

### Etape 4 — Service applicatif

Objectif : composer la premiere chaine de build complete.

A faire :

- creer `build_project(root, target="markdown", ...) -> BuildResult` ou une
  API equivalente ;
- reutiliser le tronc projet du pipeline partage ;
- executer le lint avant le builder ;
- reutiliser exactement la politique `has_errors(...)` deja appliquee en phase
  4 ;
- court-circuiter l'assemblage et l'ecriture en cas d'erreur ;
- conserver les diagnostics amont dans le `BuildResult` final.

### Etape 5 — CLI `scribpy build markdown`

Objectif : exposer la capacite de build a l'utilisateur.

A faire :

- ajouter le sous-arbre de commandes `build markdown` ;
- accepter `--root` ;
- appeler le service applicatif plutot que le builder directement ;
- afficher les diagnostics sur stderr ;
- afficher l'artefact produit sur stdout ;
- retourner :
  - `0` si le build reussit ;
  - `1` si des diagnostics bloquants empechent ou font echouer le build ;
  - `2` pour un mauvais usage CLI.

### Etape 6 — Tests et qualite

Objectif : verrouiller la premiere chaine de build avant la phase 6.

A faire :

- tests unitaires d'assemblage ;
- tests du builder Markdown ;
- tests du service applicatif avec projet valide et invalide ;
- tests CLI ;
- verification que la couverture reste a 100% ;
- passage de `make check`.

---

## Consequences

### Positives

- Scribpy produit son premier artefact utilisateur complet ;
- la chaine `scan -> parse -> lint -> assemble -> build` devient observable de
  bout en bout ;
- les phases suivantes pourront faire evoluer le contenu avec un resultat visible
  immediat ;
- la separation entre transformation, assemblage et ecriture est posee avant
  l'arrivee des cibles HTML/PDF.

### Trade-offs acceptes

- la frontiere de transformation existe avant que les vraies transformations ne
  soient disponibles ;
- l'artefact Markdown initial reste volontairement sobre et proche des sources ;
- le service de build doit composer lint et build sans encore beneficier d'un
  registre complet de builders.

Ces couts sont acceptes car ils evitent de melanger trop tot deux decisions
independantes : produire un premier artefact fiable, puis enrichir la chaine de
transformation.

---

## Criteres d'acceptation

La phase 5 est consideree terminee lorsque :

1. `scribpy build markdown` produit `build/markdown/document.md` sur un projet
   valide ;
2. l'ordre du fichier assemble suit le `DocumentIndex` ;
3. aucun artefact n'est ecrit si la preparation projet ou le lint contient une
   erreur ;
4. `build_project(...)` retourne un `BuildResult` coherent avec les diagnostics
   et artefacts produits ;
5. le builder Markdown n'introduit aucune transformation visible reservee a la
   phase 6 ;
6. les tests couvrent la logique pure, le service applicatif et le CLI ;
7. `make check` passe avec 100% de couverture.

---

## Decisions differees

Les decisions suivantes sont explicitement repoussees a la phase 6 ou au-dela :

- la forme finale de `TransformedDocument` si le contrat minimal de phase 5 ne
  suffit plus ;
- l'ordre configurable des transforms ;
- la generation de TOC ;
- la numerotation de sections ;
- la reecriture de liens par cible ;
- la configuration multi-cibles du build ;
- la selection de builders via registre d'extensions.

Ce report est intentionnel : la phase 5 doit valider le squelette de build avant
d'ajouter des comportements qui modifieront le contenu.
