# ADR-0002 — Planification de la phase 3 : parsing et extraction semantique

**Date:** 2026-05-06  
**Statut:** propose  
**Decideurs:** Antoine Barre  
**References:** `doc/FUNCTIONAL_CHAINS.md`, `doc/SDD.md`, `doc/adr/ADR-0001-phase-2-project-context-chain.md`

---

## Contexte

`doc/FUNCTIONAL_CHAINS.md` definit la phase 3 comme la chaine fonctionnelle
FC-03 Parse and Extract Document Semantics.

La phase 2 etablit le contexte projet, la configuration, la decouverte des
sources Markdown et un `DocumentIndex` deterministe. La phase 3 doit maintenant
transformer ces `SourceFile` en `Document` exploitables par les phases suivantes
de lint, transformation, assemblage et build.

Dans `doc/FUNCTIONAL_CHAINS.md`, FC-03 couvre :

```text
SourceFile[]
  -> read_text
  -> parse_frontmatter
  -> parse_markdown
  -> extract_headings
  -> extract_links
  -> extract_assets
  -> Document[]
```

Cette phase est volontairement limitee : elle ne valide pas encore la qualite
documentaire et ne modifie pas les sources. Elle produit un modele semantique
stable, avec diagnostics, que `lint`, `transforms`, `assets` et `builders`
pourront consommer.

---

## Decision

La phase 3 sera implementee comme une tranche verticale complete :

```text
Project + DocumentIndex -> read source -> frontmatter -> Markdown AST -> semantic extraction -> Document[]
```

Le livrable principal sera une capacite applicative reutilisable :

```python
parse_project_documents(project, services) -> ParseResult
```

Cette operation devra :

- lire les fichiers Markdown references par le `DocumentIndex` ;
- separer le frontmatter du corps Markdown ;
- parser le corps Markdown via le protocole `MarkdownParser` ;
- extraire les titres, liens Markdown, images et references d'assets ;
- produire des `Document` immuables ;
- conserver les chemins absolus et relatifs issus de la phase 2 ;
- retourner les erreurs utilisateur sous forme de `Diagnostic`.

La phase 3 introduira un parser par defaut leger et interne pour le MVP. Il
devra couvrir les besoins d'extraction de base sans ajouter de dependance
obligatoire. Le protocole `MarkdownParser` restera le point d'injection pour un
adaptateur plus complet, par exemple `markdown-it-py`, dans une phase
ulterieure.

---

## Perimetre Fonctionnel

### Inclus

- `scribpy.parser`
  - `parse_frontmatter` ;
  - `parse_markdown` ;
  - parser Markdown par defaut minimal ;
  - `parse_document_file` ;
  - `parse_documents`.

- `scribpy.model`
  - utilisation des types existants `Document`, `MarkdownAst`, `Heading`,
    `Reference` et `AssetRef` ;
  - ajout eventuel d'un `ParseResult` si necessaire pour agreger documents et
    diagnostics.

- Extraction semantique
  - titres ATX `#` a `######` ;
  - ancres normalisees pour les titres ;
  - liens inline Markdown `[text](target)` ;
  - images inline Markdown `![alt](target)` ;
  - references locales converties en `Path` quand c'est applicable ;
  - assets image detectes comme `AssetRef(kind="image")`.

- Frontmatter
  - detection du bloc delimite par `---` en tete de fichier ;
  - parsing minimal en dictionnaire pour les paires simples `key: value` ;
  - diagnostic en cas de bloc non ferme ou ligne non interpretable.

- CLI et core
  - exposition minimale pour verifier que le parsing fonctionne de bout en bout,
    soit via une commande dediee `scribpy parse check`, soit via une facade
    `core.parse_project_documents` appelee par les tests.

- Tests
  - frontmatter absent, valide et invalide ;
  - extraction de titres et ancres ;
  - extraction de liens internes, liens externes et images ;
  - parsing multi-fichiers dans l'ordre du `DocumentIndex` ;
  - diagnostics pour fichier illisible ou erreur de parsing.

### Exclus

- lint documentaire (`LINT001`, `LINT002`, `LINT003`, etc.) ;
- resolution effective des liens internes entre documents ;
- validation d'existence des assets ;
- parsing Markdown complet CommonMark ;
- transformation de contenu ;
- generation d'artefacts ;
- rendu HTML, PDF ou diagrammes ;
- systeme d'extensions.

---

## Etat Actuel

Deja disponible :

- `SourceFile` ;
- `Document` ;
- `MarkdownAst` ;
- `Heading` ;
- `Reference` ;
- `AssetRef` ;
- protocole `MarkdownParser` ;
- paquet `scribpy.parser` avec un contrat documentaire mais sans
  implementation ;
- paquet de compatibilite `scribpy.parsers`, marque deprecie ;
- diagnostics et resultats typables dans `model`.

A creer ou completer :

- implementation de `parse_frontmatter` ;
- implementation de `parse_markdown` ;
- parser Markdown minimal conforme au protocole ;
- fonctions `extract_headings`, `extract_links`, `extract_assets` ;
- fonction `parse_document_file` ;
- fonction `parse_documents` ;
- resultat applicatif de parsing si le type existant ne suffit pas ;
- tests unitaires et tests de chaine avec un projet temporaire.

---

## Plan de Realisation

### Etape 1 — Resultat de parsing

Objectif : definir le contrat retourne aux couches applicatives.

A faire :

- verifier si `model.results` peut accueillir un resultat specialise ;
- ajouter `ParseResult` si necessaire avec :
  - `documents: tuple[Document, ...]` ;
  - `diagnostics: tuple[Diagnostic, ...]` ;
  - `failed: bool`.
- garder le type immuable et coherent avec `LintResult` et `BuildResult`.

Diagnostics attendus :

- `PRS001` : fichier source illisible ;
- `PRS002` : frontmatter invalide ;
- `PRS003` : erreur de parsing Markdown ;
- `PRS004` : extraction semantique incomplete ou incoherente.

### Etape 2 — Frontmatter minimal

Objectif : separer les metadonnees du contenu Markdown.

A faire :

- detecter uniquement le frontmatter place en tout debut de fichier ;
- accepter l'absence de frontmatter ;
- retourner `frontmatter` et `body` sans perdre les numeros de ligne utiles ;
- parser les paires simples `key: value` ;
- diagnostiquer les blocs ouverts non fermes.

Contraintes :

- ne pas ajouter PyYAML comme dependance obligatoire dans cette phase ;
- documenter que le parsing frontmatter est volontairement minimal pour le MVP.

### Etape 3 — Parser Markdown par defaut

Objectif : produire un `MarkdownAst` exploitable par les extracteurs.

A faire :

- creer une classe ou fonction adapter conforme a `MarkdownParser` ;
- produire des tokens simples et stables pour :
  - heading ;
  - paragraph/text ;
  - link ;
  - image ;
  - fenced_code si utile pour les futures phases assets/diagrammes.
- conserver le `backend` sous une valeur explicite, par exemple
  `"scribpy-minimal"`.

### Etape 4 — Extraction semantique

Objectif : remplir les collections semantiques du `Document`.

A faire :

- extraire les `Heading` avec niveau, titre, ancre et ligne ;
- normaliser les ancres de maniere deterministe ;
- extraire les `Reference` depuis les liens inline ;
- distinguer liens externes, ancres locales et chemins relatifs ;
- extraire les `AssetRef` depuis les images ;
- conserver les cibles brutes telles qu'ecrites dans le Markdown.

### Etape 5 — Construction de `Document`

Objectif : convertir chaque `SourceFile` en objet `Document`.

A faire :

- lire le texte via le `FileSystem` injecte ;
- parser frontmatter et corps Markdown ;
- construire l'AST ;
- executer les extracteurs ;
- determiner `title` depuis `frontmatter["title"]` ou le premier H1 ;
- agreger les diagnostics sans interrompre tout le lot quand un fichier echoue.

### Etape 6 — Parsing projet et API

Objectif : fournir l'operation de chaine utilisable par les phases suivantes.

A faire :

- implementer `parse_documents(files, services)` ;
- garantir l'ordre identique a celui du `DocumentIndex` ;
- exposer une facade `core` minimale si elle clarifie l'usage ;
- ajouter une commande CLI de verification seulement si elle apporte une valeur
  immediate sans elargir excessivement le perimetre.

### Etape 7 — Tests et qualite

Objectif : verrouiller le contrat avant le lint.

A faire :

- tester les fonctions d'extraction de facon isolee ;
- tester un document complet avec frontmatter, titres, liens et images ;
- tester plusieurs fichiers ordonnes par index ;
- tester les diagnostics d'erreur utilisateur ;
- lancer `make check`.

---

## Criteres de Sortie

La phase 3 est terminee lorsque :

- un ensemble de `SourceFile` indexe peut etre parse en `Document[]` ;
- le frontmatter minimal est extrait ou diagnostique ;
- les titres ATX sont extraits avec niveau, ligne et ancre stable ;
- les liens Markdown inline sont extraits comme `Reference` ;
- les images Markdown inline sont extraites comme `AssetRef` ;
- les erreurs de lecture, frontmatter et parsing sont retournees en
  diagnostics ;
- l'ordre des documents respecte le `DocumentIndex` ;
- l'API de parsing est utilisable par la future phase 4 de lint ;
- les tests couvrent les cas nominaux et les principaux echecs utilisateur ;
- `make check` passe.

---

## Consequences

Consequences positives :

- la phase 4 pourra implementer les regles de lint sur un modele semantique
  stable ;
- les phases de transformation et build n'auront pas a relire ou reparcourir
  les sources brutes ;
- le parser externe reste substituable grace au protocole existant ;
- Scribpy gagne une separation claire entre lecture, parsing et validation
  documentaire.

Compromis :

- le parser minimal ne couvrira pas tout CommonMark ;
- le frontmatter sera limite aux cas simples tant qu'aucune dependance YAML
  n'est choisie ;
- certaines validations utiles, comme les liens casses ou assets manquants,
  resteront hors perimetre jusqu'a la phase 4 ou 9 ;
- le format exact des tokens `MarkdownAst` devra rester assez simple pour ne pas
  figer trop tot une representation interne.

Risques :

- une extraction par expressions regulieres peut diverger des regles Markdown
  completes ;
- les numeros de ligne peuvent devenir faux si le frontmatter est retire sans
  compensation ;
- l'ancrage des titres peut ne pas correspondre aux conventions de tous les
  renderers ;
- ajouter trop vite un parser tiers peut alourdir l'installation de base.

Mitigations :

- limiter explicitement le MVP aux syntaxes supportees ;
- conserver la cible brute dans les `Reference` et `AssetRef` ;
- tester les numeros de ligne avec et sans frontmatter ;
- isoler la generation d'ancre dans une fonction dediee ;
- garder `MarkdownParser` comme frontiere d'injection pour remplacer le backend
  sans changer les phases aval.

---

## Decisions Ouvertes

1. Nom exact de la facade publique : `parse_project_documents`,
   `parse_documents` ou `load_documents`.
2. Ajout ou non d'une commande CLI de diagnostic `scribpy parse check` pendant
   la phase 3.
3. Convention d'ancres a adopter par defaut : GitHub-compatible ou convention
   propre a Scribpy.
4. Moment d'introduction d'une dependance optionnelle `markdown-it-py`.
5. Niveau de severite pour un frontmatter invalide : erreur bloquante ou warning
   si le corps Markdown reste exploitable.

Proposition initiale :

- utiliser `parse_project_documents` pour l'operation de haut niveau ;
- repousser la commande CLI si `scribpy lint` est prevu immediatement en phase 4 ;
- utiliser une normalisation d'ancre compatible GitHub pour reduire la surprise
  utilisateur ;
- garder le frontmatter invalide en erreur, car les metadonnees peuvent piloter
  les phases de build.

---

## Sequence Recommandee de Pull Requests

1. `parse-result-and-frontmatter`
   - resultat de parsing ;
   - diagnostics `PRS` ;
   - parsing frontmatter minimal ;
   - tests dedies.

2. `minimal-markdown-parser`
   - parser par defaut conforme a `MarkdownParser` ;
   - tokens heading/link/image ;
   - tests du backend minimal.

3. `semantic-extractors`
   - extraction titres, ancres, liens et assets ;
   - tests de normalisation et de lignes.

4. `document-parser-chain`
   - `parse_document_file` ;
   - `parse_documents` ;
   - conservation de l'ordre du `DocumentIndex` ;
   - tests de chaine.

5. `core-parse-api`
   - facade `core` si retenue ;
   - eventuelle commande de verification ;
   - tests d'integration ;
   - `make check`.

Cette sequence transforme FC-03 en capacite exploitable sans melanger la phase 3
avec le lint documentaire de la phase 4.
