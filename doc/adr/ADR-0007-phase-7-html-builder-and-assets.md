# ADR-0007 — Planification de la phase 7 : sorties HTML single-page et site MkDocs

**Date:** 2026-05-16  
**Statut:** propose  
**Decideurs:** Antoine Barre  
**References:** `doc/FUNCTIONAL_CHAINS.md`, `doc/SDD.md`, `doc/adr/ADR-0005-phase-5-first-build-artifact-markdown.md`, `doc/adr/ADR-0006-phase-6-transform-pipeline.md`

---

## Contexte

`doc/FUNCTIONAL_CHAINS.md` definit la phase 7 comme le premier livrable de
consultation web. Les phases precedentes rendent deja Scribpy capable de :

1. charger un projet et construire un `DocumentIndex` deterministe ;
2. parser les sources Markdown et extraire leur semantique ;
3. executer le lint natif avant build ;
4. produire un artefact Markdown assemble ;
5. transformer le contenu selon la cible, avec titre global, TOC, numerotation et
   reecriture de liens configurables.

La phase 7 doit maintenant produire une sortie web sans confondre deux usages
qui ont des besoins differents :

1. un **livrable HTML simple et autonome**, adapte a la previsualisation ou a la
   diffusion d'un document unique ;
2. une **base de site documentaire**, adaptee a une navigation multi-page et a
   l'ecosysteme MkDocs.

Dans `doc/FUNCTIONAL_CHAINS.md`, FC-07 couvre le rendu HTML :

```text
AssembledDocument + Theme + CSS
  -> load_theme
  -> resolve_css_files
  -> render_template
  -> HtmlRenderer.render
  -> write build/html/index.html
```

La phase 7 reprend aussi la partie immediate de FC-09 necessaire au web :
validation et copie des assets references, ainsi que le rendu de diagrammes
utile au HTML : **PlantUML** et **Mermaid** via des plugins internes de blocs de
code.

MkDocs fournit deja un modele standard pour un site documentaire : un fichier
`mkdocs.yml`, un repertoire `docs/`, une navigation `nav`, des liens Markdown
relatifs entre pages et des CSS additionnels declares via `extra_css`. Scribpy
peut donc generer une base MkDocs valide sans devoir reimplementer un moteur de
site complet. 

---

## Decision

La phase 7 introduira **deux modes de sortie HTML distincts** :

| Mode | Objectif | Sortie principale |
|---|---|---|
| `single-page` | produire un document HTML autonome | `build/html/index.html` |
| `site` | produire un site HTML via MkDocs encapsule par Scribpy | `build/site/site/` |

Le livrable utilisateur sera expose via :

```text
scribpy build html --mode single-page
scribpy build html --mode site
```

ou une API equivalente dans `build_project(...)`.

### Plugins internes de blocs de code et rendu PlantUML

La phase 7 introduira une abstraction interne de **plugins de blocs de code**.
PlantUML sera la premiere implementation, mais le mecanisme devra aussi pouvoir
accueillir Mermaid ou d'autres langages fenced qui produisent des artefacts puis
remplacent leur bloc source dans le Markdown transforme :

```text
Markdown avec blocs fenced pris en charge
  -> CodeBlockPlugin.has_blocks
  -> CodeBlockPlugin.preflight
  -> CodeBlockPlugin.render_documents
  -> generated local assets
  -> replace blocks with local HTML/image references
  -> HTML final
```

La fonction centrale attendue sera :

```python
render_plantuml_blocks(
    content: str,
    *,
    renderer: DiagramRenderer,
    output_dir: Path,
) -> PlantUmlRenderResult
```

`PlantUmlRenderResult` contiendra le contenu reecrit, les assets produits et les
diagnostics associes. Le plugin PlantUML devra :

- detecter les blocs fenced `plantuml` presents dans le Markdown ;
- choisir le renderer PlantUML configure (`web` par defaut, `java` sur demande) ;
- produire des assets SVG locaux deterministes ;
- remplacer les blocs sources par du HTML ou des references d'image locales ;
- retourner les diagnostics de rendu sans muter les sources ;
- verifier Java au plus tot lorsque le backend `java` est explicitement demande.

Le choix SVG est retenu pour le MVP HTML : il reste lisible, vectoriel et
portable dans les deux modes de sortie. L'integration de PlantUML appartient a
Scribpy ; le backend de rendu reste un adaptateur derriere le protocole
`DiagramRenderer`, afin de conserver un pipeline testable. Le mode `web`
favorise l'usage immediat ; le mode `java` preserve un chemin hors ligne quand
le projet l'exige.

### Mode `single-page`

Le mode `single-page` sera implemente comme une vraie cible de rendu HTML :

```text
project parse pipeline -> lint -> single-page transforms -> assemble -> html render -> asset copy -> artifacts
```

Il devra :

- reutiliser le pipeline projet partage ;
- executer le lint avant toute ecriture d'artefact ;
- preparer une vue documentaire unique ;
- conserver un seul H1 global, la TOC et la numerotation configurees par
  `[document]` ;
- resoudre les liens inter-documents vers des ancres internes de la page unique ;
- accepter un ou plusieurs fichiers CSS fournis par le projet ;
- copier ces CSS dans la sortie ou les embarquer selon la strategie retenue ;
- rendre `build/html/index.html` ;
- copier les assets locaux vers `build/html/assets/` ;
- reecrire les liens d'assets pour qu'ils restent valides dans la sortie finale.

### Mode `site`

Le mode `site` utilisera MkDocs comme moteur de rendu externe **encapsule par
Scribpy** :

```text
project parse pipeline -> lint -> site transforms -> materialize docs tree -> write mkdocs.yml -> copy assets/css -> mkdocs build -> artifacts
```

Il devra :

- conserver une structure multi-page ;
- produire `build/site/mkdocs.yml` ;
- produire `build/site/docs/` avec les documents Markdown transformes ;
- generer `nav` a partir de l'ordre du `DocumentIndex` ;
- preserver les chemins relatifs des pages sous `docs/` ;
- conserver les liens Markdown relatifs compatibles avec MkDocs ;
- copier les assets statiques sous `build/site/docs/` ;
- copier les CSS projet sous `build/site/docs/css/` ou conserver leur chemin
  relatif valide ;
- declarer les CSS fournis dans `extra_css` ;
- invoquer `mkdocs build` depuis Scribpy pour produire le site HTML final sous
  `build/site/site/`.

MkDocs transforme nativement les liens Markdown relatifs vers les pages HTML
correspondantes lors de son build, et attend que les chemins de `nav` soient
relatifs a `docs_dir`. Il copie egalement les fichiers non-Markdown presents dans
`docs_dir`, dont les CSS declares via `extra_css`. Le mode `site` doit s'appuyer
sur ces conventions plutot que les contourner. 

---

## Perimetre Fonctionnel

### Inclus

- `scribpy.config`
  - section minimale `[builders.html]` ;
  - choix `mode = "single-page" | "site"` ;
  - fichiers CSS fournis en entree ;
  - chemins de sortie par mode ;
  - options MkDocs minimales utiles au mode `site`.

- `scribpy.transforms`
  - jeu `single-page` : normalisation de la hierarchie assemblee, resolution des
    liens vers ancres internes, TOC et numerotation ;
  - jeu `site` : conservation de la structure multi-page et des liens Markdown
    relatifs compatibles MkDocs ;
  - plugins de rendu de blocs de code communs aux sorties HTML, executes avant
    la reecriture finale des liens et le rendu HTML ;
  - reutilisation de la configuration `[document]` pour TOC et numerotation quand
    elle s'applique au mode choisi.

- `scribpy.builders`
  - builder HTML `single-page` ;
- generation du squelette MkDocs puis invocation de MkDocs en mode `site` ;
  - ecriture des artefacts propres a chaque mode.

- `scribpy.themes`
  - template HTML par defaut pour `single-page` ;
  - resolution des CSS d'entree ;
  - aucun moteur de theme complet requis pour le mode `site` MVP.

- `scribpy.assets`
  - collecte des assets references ;
  - validation des assets locaux ;
  - rendu PlantUML en SVG via `render_plantuml_blocks(...)` ;
  - rendu Mermaid web-only en SVG via `render_mermaid_blocks(...)` ;
  - copie vers la destination adaptee au mode :
    - `build/html/assets/` pour `single-page` ;
    - `build/site/docs/...` pour `site` ;
  - diagnostics de copie.

- `scribpy.core`
  - extension de `build_project(...)` pour les deux modes HTML ;
  - reutilisation du pipeline projet et du lint ;
  - orchestration explicite differenciee par mode ;
  - propagation uniforme des diagnostics.

- `scribpy.cli`
  - `scribpy build html --mode single-page` ;
  - `scribpy build html --mode site` ;
  - `--root` coherent avec les autres commandes ;
  - affichage des artefacts produits.

- Tests
  - configuration HTML ;
  - rendu single-page ;
  - prise en compte de CSS fourni ;
  - generation de la base MkDocs ;
  - `mkdocs.yml`, `docs/`, `nav` et `extra_css` ;
  - copie d'assets ;
  - comportement des liens par mode ;
  - integration applicative ;
  - comportement CLI.

### Exclus

- execution automatique de `mkdocs serve` ;
- HTML multi-page rendu directement par Scribpy ;
- moteur de theme MkDocs personnalise ;
- rendu PDF ;
- rendu Mermaid ;
- bundling/minification CSS ou JavaScript ;
- recherche client-side ;
- preview server integre ;
- registre complet de builders ;
- decouverte dynamique de plugins.

---

## Etat Actuel

Deja disponible :

- `build_project(...)` pour `target="markdown"` ;
- `BuildArtifact`, `BuildResult` et `AssembledDocument` ;
- pipeline de transformation cible-aware ;
- transformation single-page deja amorcee par la logique de liens internes et de
  vue assemblee ;
- validation d'assets locaux via le lint natif `LINT004` ;
- protocoles `HtmlRenderer` et `FileSystem` ;
- paquets `scribpy.assets` et `scribpy.themes` encore principalement
  documentaires ;
- commandes CLI jusqu'a `scribpy build markdown`.

A creer ou completer :

- types de configuration HTML et de mode ;
- `TransformOptions` ou equivalent pour les decisions propres aux modes HTML ;
- builder `single-page` ;
- generation du squelette MkDocs ;
- resolution et copie des CSS d'entree ;
- copie d'assets adaptee a chaque mode ;
- extension de `build_project(...)` et du CLI ;
- tests unitaires et de chaine associes.

---

## Regles MVP

| Sujet | `single-page` | `site` |
|---|---|---|
| Nature | document HTML autonome | site HTML multi-page via MkDocs |
| Sortie principale | `build/html/index.html` | `build/site/site/` |
| Documents | assembles en une page | conserves en pages distinctes |
| Liens inter-documents | ancres internes | liens Markdown relatifs conserves |
| CSS | fichiers d'entree references/copied | fichiers d'entree copies et declares via `extra_css` |
| Assets | `build/html/assets/` | `build/site/docs/...` |
| Diagrammes | SVG locaux sous `assets/diagrams/` | SVG locaux sous `docs/assets/diagrams/` |
| Navigation | TOC du document assemble | `nav` MkDocs depuis `DocumentIndex` |
| Rendu HTML final | par Scribpy | par MkDocs, pilote par Scribpy |

Principes communs :

- les deux modes reutilisent le meme tronc projet et les memes diagnostics ;
- les transforms restent responsables de la preparation du contenu, pas de
  l'ecriture des fichiers ;
- les CSS fournis sont des entrees de projet, pas des dependances codees en dur ;
- les blocs pris en charge sont traites par des plugins internes ordonnes ;
- le mode `site` s'appuie sur les conventions MkDocs au lieu de les repliquer ;
- les outputs restent deterministes a configuration et sources identiques.

---

## Plan de Realisation

### Etape 1 — Configuration HTML par mode

Objectif : rendre explicites les deux strategies de publication.

A faire :

- introduire les types minimaux de `[builders.html]` ;
- definir `mode = "single-page" | "site"` ;
- ajouter les CSS d'entree ;
- definir les chemins de sortie par mode ;
- valider les valeurs et chemins utilisateur.

### Etape 2 — Pipeline de contenu par mode

Objectif : eviter qu'un meme jeu de transforms serve deux usages incompatibles.

A faire :

- conserver en `single-page` la resolution vers ancres internes ;
- conserver en `site` les pages distinctes et les liens Markdown relatifs ;
- reutiliser `[document.toc]` et `[document.numbering]` selon la strategie
  retenue ;
- documenter les differences de comportement entre modes.

### Etape 3 — Builder `single-page`

Objectif : produire le livrable HTML autonome.

A faire :

- assembler les documents transformes ;
- rendre le Markdown assemble en HTML ;
- integrer les references HTML locales produites pour les diagrammes PlantUML ;
- injecter le contenu dans un template HTML par defaut ;
- integrer ou referencer les CSS d'entree ;
- ecrire `build/html/index.html` ;
- copier les assets et reecrire leurs chemins.

Diagnostics proposes :

- `BLD004` : echec de rendu HTML ;
- `BLD005` : echec d'ecriture de l'artefact HTML ;
- `CSS001` : fichier CSS configure introuvable ;
- `CSS002` : echec de copie CSS.

### Etape 4 — Builder `site` MkDocs

Objectif : produire le site final en pilotant MkDocs depuis Scribpy.

A faire :

- materialiser les documents transformes sous `build/site/docs/` ;
- generer `build/site/mkdocs.yml` ;
- produire `nav` dans l'ordre du `DocumentIndex` ;
- copier les assets et CSS dans `docs/` ;
- copier les SVG PlantUML generes dans `docs/assets/diagrams/` ;
- declarer `extra_css` ;
- lancer `mkdocs build` sur le squelette genere ;
- retourner des artefacts pour `mkdocs.yml`, les pages, les ressources et le site
  HTML final.

Diagnostics proposes :

- `SITE001` : echec de generation de `mkdocs.yml` ;
- `SITE002` : echec d'ecriture d'une page du site ;
- `SITE003` : MkDocs indisponible ou echec de son rendu.

### Etape 5 — Plugins de blocs et rendu PlantUML

Objectif : transformer les blocs de code supportes du Markdown en assets HTML
via une architecture interne extensible.

A faire :

- introduire le protocole `CodeBlockPlugin` ;
- permettre l'enregistrement de plugins dans `ExtensionRegistry` ;
- detecter les fences `plantuml` dans les documents transformes ;
- ajouter `render_plantuml_blocks(...)` comme point d'entree de rendu ;
- utiliser un `DiagramRenderer` injecte ;
- choisir `web` par defaut et `java` lorsque ce backend est explicitement
  configure ;
- verifier la disponibilite de Java avant rendu quand `java` est selectionne ;
- produire des fichiers SVG deterministes sous `assets/diagrams/` ;
- remplacer les fences par des references HTML locales ;
- exposer les assets produits au builder `single-page` et au builder `site` ;
- garantir le fonctionnement hors ligne du backend `java` par des tests sans
  acces reseau.

Diagnostics proposes :

- `UML001` : bloc PlantUML invalide ou non ferme ;
- `UML002` : echec de rendu PlantUML Java ;
- `UML003` : echec d'ecriture d'un SVG genere.
- `UML004` : runtime Java indisponible ;
- `UML005` : echec de rendu PlantUML web.
- `MRM001` : bloc Mermaid invalide ou non ferme ;
- `MRM002` : echec de rendu Mermaid web ;
- `MRM003` : echec d'ecriture d'un SVG Mermaid genere.

### Etape 6 — Service applicatif et CLI

Objectif : exposer les deux modes sans dupliquer la logique metier.

A faire :

- etendre `build_project(...)` pour les modes HTML ;
- garder une politique de blocage uniforme ;
- ajouter `scribpy build html --mode single-page` ;
- ajouter `scribpy build html --mode site` ;
- afficher les artefacts produits.

### Etape 7 — Tests et qualite

Objectif : verrouiller les deux chemins avant d'ouvrir le PDF.

A faire :

- tests de config ;
- tests du rendu single-page ;
- tests de CSS d'entree ;
- tests du squelette MkDocs et de `nav` ;
- tests d'assets par mode ;
- tests de detection et de rendu PlantUML ;
- tests de detection, logs et diagnostics du rendu Mermaid web-only ;
- tests du service applicatif ;
- tests CLI ;
- `make check` avec 100% de couverture.

---

## Consequences

### Positives

- Scribpy couvre deux usages web reels sans les confondre ;
- le mode `single-page` reste simple et autonome ;
- le mode `site` beneficie immediatement de l'ecosysteme MkDocs ;
- les diagrammes PlantUML peuvent etre publies en mode web immediat ou en mode
  Java hors ligne ;
- Mermaid partage le meme pipeline de plugins sans changer les builders HTML ;
- les CSS deviennent une vraie entree configurable ;
- la future evolution vers un site complet ne demande pas de rearchitecturer le
  builder single-page.

### Trade-offs acceptes

- deux chemins de build doivent etre maintenus des la phase 7 ;
- le mode `site` produit une base, pas encore le site HTML final ;
- certaines options `[document]` n'ont pas exactement la meme portee selon le
  mode ;
- les tests doivent verifier explicitement deux comportements de liens
  differents ;
- les integrations de diagrammes ajoutent des backends web et Java a
  diagnostiquer proprement.

Ces couts sont acceptes car ils correspondent a deux besoins utilisateurs
legitimes et evitent de forcer un seul modele HTML a couvrir deux usages
incompatibles.

---

## Criteres d'acceptation

La phase 7 est consideree terminee lorsque :

1. `scribpy build html --mode single-page` produit `build/html/index.html` ;
2. le mode `single-page` accepte du CSS d'entree et le rend disponible dans la
   sortie ;
3. le mode `single-page` resout les liens inter-documents vers des ancres
   internes ;
4. `scribpy build html --mode site` produit `build/site/mkdocs.yml` et
   `build/site/docs/` ;
5. le mode `site` genere une navigation MkDocs ordonnee depuis le
   `DocumentIndex` ;
6. le mode `site` copie les CSS fournis et les declare dans `extra_css` ;
7. le mode `site` preserve des liens Markdown relatifs compatibles avec MkDocs ;
8. les assets locaux sont copies dans la destination attendue par chaque mode ;
9. les blocs de code supportes sont traites par des plugins internes
   extensibles ;
10. les blocs `plantuml` presents dans le Markdown sont rendus en SVG puis
    integres a la sortie HTML ;
11. PlantUML utilise le backend `web` par defaut et peut etre force sur `java`
    pour un usage hors ligne ;
12. le backend PlantUML `java` verifie son environnement avant le rendu ;
13. les blocs `mermaid` sont rendus en SVG via un backend web uniquement ;
14. aucun artefact n'est ecrit en cas d'erreur bloquante ;
15. les tests couvrent config, transforms, builders, assets, service applicatif
    et CLI ;
16. `make check` passe avec 100% de couverture.

---

## Decisions differees

Les decisions suivantes sont explicitement repoussees a la phase 8 ou au-dela :

- execution automatique de `mkdocs serve` ou `mkdocs build` ;
- rendu PDF ;
- rendu Mermaid ;
- generation de themes MkDocs personnalises ;
- bundling/minification CSS ou JavaScript ;
- recherche client-side ;
- serveur de preview integre ;
- registre complet de builders ;
- decouverte dynamique de plugins.

Ce report est intentionnel : la phase 7 doit etablir deux sorties web utiles,
claires et testables avant d'ajouter des integrations d'execution plus lourdes.
