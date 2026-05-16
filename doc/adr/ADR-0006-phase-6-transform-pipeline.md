# ADR-0006 — Planification de la phase 6 : pipeline de transformation

**Date:** 2026-05-16  
**Statut:** accepte  
**Decideurs:** Antoine Barre  
**References:** `doc/FUNCTIONAL_CHAINS.md`, `doc/SDD.md`, `doc/adr/ADR-0004-result-pipeline-functional-chains.md`, `doc/adr/ADR-0005-phase-5-first-build-artifact-markdown.md`

---

## Contexte

`doc/FUNCTIONAL_CHAINS.md` definit la phase 6 comme l'introduction du
comportement d'ingenierie documentaire dans Scribpy.

Les phases precedentes rendent deja Scribpy capable de :

1. charger un projet et construire un `DocumentIndex` deterministe ;
2. parser les sources Markdown et extraire leur semantique ;
3. executer le lint natif avant build ;
4. produire un premier artefact Markdown assemble ;
5. conserver une frontiere minimale entre documents parses et documents prets a
   assembler via `TransformedDocument`.

La phase 5 a volontairement livre un artefact tres proche des sources afin de
valider la premiere chaine complete de build. La phase 6 doit maintenant donner
une valeur visible a la frontiere de transformation deja posee : enrichir le
contenu sans muter les fichiers d'origine, avant assemblage et avant les futurs
builders HTML/PDF.

Dans `doc/FUNCTIONAL_CHAINS.md`, FC-05 couvre :

```text
Document[]
  -> resolve_includes
  -> resolve_cross_references
  -> apply_section_numbering
  -> render_diagrams
  -> rewrite_links_for_target
  -> generate_toc_transform
  -> TransformedDocument[]
```

La feuille de route de la phase 6 retient pour ce jalon :

1. generation de table des matieres ;
2. numerotation des sections ;
3. resolution des references internes ;
4. reecriture des liens selon la cible ;
5. registre de transformations.

Cette phase ne doit pas encore melanger le pipeline de transformation avec les
responsabilites plus lourdes des phases suivantes : rendu HTML, copie d'assets,
rendu de diagrammes ou build PDF.

---

## Decision

La phase 6 sera implementee comme une evolution explicite de la chaine de build
existante :

```text
project parse pipeline -> lint -> ordered transform pipeline -> assemble -> artifact
```

Le livrable principal sera un pipeline de transformation ordonne,
dependant de la cible et sans mutation des sources :

```python
apply_transforms(documents, target=..., transforms=...) -> TransformResult
```

Chaque transformation devra :

- recevoir un `TransformContext` contenant les documents sources, les valeurs
  transformees courantes et la cible de build ;
- retourner un `TransformResult` avec de nouveaux `TransformedDocument` et ses
  diagnostics propres ;
- produire de nouvelles valeurs plutot que modifier les `Document` d'origine ;
- etre executee dans un ordre deterministe fourni par un registre ;
- pouvoir etre remplacee ou completee sans coupler le builder Markdown a son
  implementation concrete.

Pour la cible Markdown, l'ordre natif retenu sera :

```text
assembled heading normalization -> section numbering -> cross-reference resolution -> table of contents
```

Pour la cible HTML preparee pour la phase suivante, l'ordre natif sera :

```text
section numbering -> target link rewriting -> table of contents
```

L'ordre retenu differe legerement de l'enumeration generique de FC-05 : la
numerotation precede la resolution des references croisees afin que les liens
soient recalcules vers les ancres finales produites par les titres numerotes.

Pour l'artefact Markdown assemble, Scribpy produira un seul titre de niveau 1 :

- le H1 global vient de `project.name` lorsqu'il est configure ;
- sinon, le titre stable `Document` est utilise ;
- les titres racine des documents sources sont abaisses d'un niveau dans la vue
  assemblee ;
- la numerotation est calculee apres cette normalisation, sur la hierarchie
  finale effectivement rendue.

La table des matieres et la numerotation seront configurables par projet via la
section `[document]` de `scribpy.toml` :

```toml
[document]
title = "My Manual"

[document.toc]
enabled = true
max_level = 3
style = "bullet"

[document.numbering]
enabled = true
max_level = 6
style = "decimal"
```

Les styles MVP retenus sont :

- TOC : `bullet`, `numbered` ;
- numerotation : `decimal`, `alpha`, `roman`.

Le reglage `document.toc.max_level` conserve explicitement le controle de
profondeur de la table des matieres. Dans l'artefact assemble, le H1 est reserve
au titre global ; la TOC porte donc sur les niveaux `##` et suivants, jusqu'au
niveau maximal configure.

Exemple :

```toml
[document.toc]
enabled = true
max_level = 3
style = "bullet"
```

Avec une hierarchie finale contenant `## Chapitre`, `### Section` et
`#### Detail`, la TOC inclut `Chapitre` et `Section`, mais exclut `Detail`.

Le choix d'un pipeline ordonne est prefere a une serie d'appels implicites dans
le builder, car la phase 6 introduit un comportement qui :

- depend de l'etat produit par les etapes precedentes ;
- doit rester observable et testable independamment de l'ecriture d'artefacts ;
- devra etre configurable et extensible lorsque les phases ulterieures ajouteront
  de nouvelles cibles ou de nouveaux transforms.

---

## Perimetre Fonctionnel

### Inclus

- `scribpy.model`
  - `TransformedDocument` comme produit de donnee pret pour une cible, distinct du
    `Document` parse ;
  - conservation d'un lien vers le `source_document` d'origine.

- `scribpy.transforms`
  - `TransformContext` ;
  - `TransformResult` ;
  - contrat `Transform` ;
  - `apply_transforms(...)` pour l'execution ordonnee ;
  - transforms natives :
    - `normalize_assembled_markdown_headings` ;
    - `apply_section_numbering` ;
    - `resolve_cross_references` ;
    - `rewrite_links_for_target` ;
    - `generate_toc_transform` ;
  - jeux natifs par cible :
    - `native_markdown_transforms()` ;
    - `native_html_transforms()` ;
  - ordre d'execution explicitement fourni au pipeline, jamais deduit par le
    builder.

- `scribpy.extensions`
  - extension de `ExtensionRegistry` pour stocker les transforms Markdown et
    HTML dans un ordre explicite ;
  - ajout de transforms Markdown supplementaires via une API immutable.

- `scribpy.core`
  - integration de `apply_transforms(...)` dans la chaine `build_project(...)`
    avant assemblage ;
  - propagation des diagnostics de transformation dans `BuildResult` ;
  - arret du build si une transformation retourne un diagnostic bloquant.

- `scribpy.config`
  - `DocumentConfig` ;
  - `TocConfig` ;
  - `NumberingConfig` ;
  - parsing et validation de `[document]`, `[document.toc]` et
    `[document.numbering]`.

- Comportements MVP
  - H1 global unique dans l'artefact Markdown assemble ;
  - abaissement d'un niveau des titres sources pour construire la vue assemblee ;
  - numerotation deterministe des titres, activable et parametree par projet ;
  - generation d'une table des matieres a partir des titres transformes,
    activable et parametree par projet ;
  - reecriture des liens inter-documents Markdown vers des ancres du document
    assemble ;
  - reecriture des liens `.md` vers `.html` pour la future cible HTML.

- Tests
  - ordre des transforms ;
  - preservation des sources ;
  - numerotation des sections ;
  - generation de TOC ;
  - resolution des references croisees ;
  - reecriture cible-specifique des liens ;
  - accumulation des diagnostics ;
  - blocage du build en cas d'erreur de transformation ;
  - chargement des transforms natifs par le registre.

### Exclus

- resolution d'includes ;
- rendu Mermaid ou PlantUML ;
- copie d'assets ;
- builder HTML complet ;
- builder PDF ;
- configuration utilisateur detaillee de l'activation ou de l'ordre des
  transforms ;
- decouverte dynamique de plugins ;
- transforms mutantes sur les fichiers sources ;
- reecriture de contenu via une AST Markdown riche.

---

## Etat Actuel

Deja disponible dans le code :

- `TransformedDocument` avec conversion depuis `Document` sans frontmatter ;
- `TransformContext`, `TransformResult` et le contrat `Transform` ;
- `apply_transforms(...)` ;
- `normalize_assembled_markdown_headings` ;
- les transforms natives de numerotation, TOC, resolution de references croisees
  et reecriture de liens par cible ;
- `native_markdown_transforms()` et `native_html_transforms()` ;
- un `ExtensionRegistry` enrichi avec `markdown_transforms` et
  `html_transforms` ;
- l'integration du pipeline de transformation dans `build_project(...)` pour la
  cible Markdown ;
- des tests couvrant les principaux comportements du pipeline.

A creer, completer ou durcir :

- formaliser l'ordre des transforms comme decision d'architecture documentee ;
- clarifier la politique de diagnostics des transforms ;
- verifier que les transforms restent bien pures et deterministes ;
- etendre le registre avec une API symetrique pour les transforms HTML si le
  builder HTML de phase 7 l'exige ;
- documenter explicitement les decisions differees vers les phases 7+ ;
- maintenir l'alignement entre la feuille de route FC-05 et l'implementation
  effective lorsque de nouveaux transforms seront ajoutes.

---

## Regles du pipeline MVP

| Sujet | Regle retenue |
|---|---|
| Produit intermediaire | les transforms consomment et retournent des `TransformedDocument` |
| Sources | les `Document` parses restent immuables et servent de reference semantique |
| Ordre | l'ordre est explicite, stable et fourni par le registre |
| Markdown | `assembled heading normalization -> section numbering -> cross-reference resolution -> TOC` |
| Structure Markdown assemblee | un seul H1 global, puis titres sources abaisses d'un niveau |
| TOC | activable, profondeur (`max_level`) et style de liste configures par `[document.toc]` |
| Numerotation | activable, profondeur et style configures par `[document.numbering]` |
| HTML prepare | `section numbering -> target link rewriting -> TOC` |
| Diagnostics | chaque transform peut produire des diagnostics accumules dans le resultat final |
| Echec | une erreur de transformation empeche l'ecriture de l'artefact |
| Determinisme | a entree et registre identiques, la sortie doit etre identique |

Principes communs :

- les transforms ne redecouvrent ni les fichiers ni l'ordre documentaire ;
- les transforms travaillent sur les valeurs deja produites par la chaine amont ;
- les liens sont reecrits selon la sortie preparee, pas selon le chemin du
  fichier source seul ;
- les transforms doivent pouvoir etre testes sans acces disque ;
- les builders assemblent ou rendent les valeurs transformees, mais ne doivent
  pas reimplementer la logique de transformation ;
- le pipeline reste assez simple pour ne pas anticiper un moteur de plugins
  complet avant la phase 9.

---

## Plan de Realisation

### Etape 1 — Stabiliser le contrat de transformation

Objectif : rendre explicite la frontiere posee en phase 5.

A faire :

- confirmer `TransformedDocument` comme produit intermediaire pret pour une cible ;
- conserver dans `TransformContext` :
  - la cible ;
  - les `Document` sources ;
  - les `TransformedDocument` courants ;
- conserver `TransformResult` comme resultat unique de chaque etape ;
- interdire toute mutation des `Document` sources dans les transforms natifs.

### Etape 2 — Executer un pipeline ordonne

Objectif : composer plusieurs transforms sans logique implicite dans les
builders.

A faire :

- appliquer les transforms dans l'ordre fourni ;
- transmettre a chaque etape le resultat produit par la precedente ;
- accumuler les diagnostics ;
- retourner les documents transformes finaux et les diagnostics associes ;
- garder l'execution synchrone et lineaire a ce stade.

### Etape 3 — Ajouter les transforms Markdown visibles

Objectif : donner une valeur utilisateur directe au premier artefact de build.

A faire :

- injecter un H1 global unique dans l'artefact assemble ;
- abaisser d'un niveau les titres des documents sources dans la vue assemblee ;
- numeroter les titres de maniere deterministe selon la configuration projet ;
- resoudre les references croisees entre documents vers des ancres compatibles
  avec l'artefact assemble ;
- generer une table des matieres configurable a partir des titres transformes ;
- conserver un reglage explicite de profondeur de TOC via
  `document.toc.max_level` ;
- verifier que le contenu produit reste stable a ordre documentaire identique.

### Etape 4 — Preparer les transforms cible-specifiques

Objectif : ne pas figer le pipeline autour du seul Markdown assemble.

A faire :

- introduire `BuildTarget` ;
- definir `rewrite_links_for_target` ;
- conserver des jeux natifs distincts pour Markdown et HTML ;
- preparer le comportement HTML sans livrer encore le builder HTML complet ;
- maintenir les transforms non pertinentes pour une cible comme no-op explicites.

### Etape 5 — Etendre le registre d'extensions

Objectif : separer la selection des transforms de leur execution.

A faire :

- charger les transforms natifs dans `ExtensionRegistry.native()` ;
- conserver l'ordre du registre comme ordre d'execution ;
- permettre l'ajout de transforms Markdown supplementaires sans modifier le
  builder ;
- garder la decouverte dynamique de plugins hors perimetre jusqu'a la phase 9.

### Etape 6 — Integrer la chaine de build et verrouiller la qualite

Objectif : faire de la phase 6 une evolution visible mais sure de la phase 5.

A faire :

- executer les transforms apres le lint et avant `merge_documents(...)` ;
- propager les diagnostics vers `BuildResult` ;
- interrompre l'ecriture d'artefact sur erreur de transformation ;
- ajouter les tests unitaires et de chaine correspondants ;
- verifier que `make check` passe.

---

## Consequences

### Positives

- Scribpy cesse d'etre seulement un assembleur et commence a produire un contenu
  reellement ingenierie ;
- les transforms deviennent observables, testables et remplacables ;
- la cible Markdown gagne immediatement de la valeur visible ;
- la phase 7 pourra reutiliser une base deja dependante de la cible au lieu d'introduire une
  seconde interpretation des liens et titres ;
- la separation `parse -> transform -> assemble -> build` devient nette dans le
  code comme dans la documentation.

### Trade-offs acceptes

- la numerotation et la TOC modifient desormais le contenu final, donc les tests
  d'artefacts deviennent plus sensibles a l'ordre des transforms ;
- certaines operations reposent encore sur des reecritures textuelles Markdown
  plutot que sur une AST riche ;
- un registre cible-specifique apparait avant que la cible HTML complete ne soit
  livree ;
- l'ordre des transforms est fixe en MVP, meme si la feuille de route vise une
  configurabilite future.

Ces couts sont acceptes car ils permettent d'obtenir une phase 6 utile sans
attendre les decisions plus larges sur HTML, assets et plugins.

---

## Criteres d'acceptation

La phase 6 est consideree terminee lorsque :

1. `apply_transforms(...)` execute plusieurs transforms dans un ordre
   deterministe ;
2. les transforms natifs retournent de nouveaux `TransformedDocument` sans
   modifier les sources ;
3. l'artefact Markdown integre la numerotation, les references internes resolues
   et une table des matieres ;
4. l'artefact Markdown contient un seul H1 global, puis une hierarchie finale
   renumerotee ;
5. `[document.toc]` permet d'activer ou non la TOC et de regler sa profondeur
   et son style ;
6. `[document.numbering]` permet d'activer ou non la numerotation et de regler
   sa profondeur et son style ;
7. le registre fournit les transforms natifs par cible ;
8. les diagnostics de transformation sont propages dans `BuildResult` ;
9. une erreur de transformation empeche l'ecriture d'un artefact ;
10. les tests couvrent la logique pure, le registre et l'integration build ;
11. `make check` passe avec 100% de couverture.

---

## Decisions differees

Les decisions suivantes sont explicitement repoussees a la phase 7 ou au-dela :

- le rendu HTML complet ;
- la copie d'assets et le rendu de diagrammes ;
- la resolution d'includes ;
- l'exposition d'une configuration utilisateur pour reordonner les transforms ;
- la separation eventuelle entre `project.name` et un futur titre de livrable
  dedie ;
- la forme finale de l'API d'enregistrement des transforms HTML ;
- la decouverte dynamique de plugins ;
- le passage eventuel de reecritures textuelles a une transformation basee sur
  une AST Markdown plus riche.

Ce report est intentionnel : la phase 6 doit etablir un pipeline de
transformation fiable avant d'ouvrir davantage sa surface de configuration et
d'extension.
