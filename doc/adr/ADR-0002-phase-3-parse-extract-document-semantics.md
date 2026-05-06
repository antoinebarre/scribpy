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

La phase 3 utilisera des bibliotheques de parsing eprouvees pour garantir
robustesse et conformite aux standards. Chaque bibliotheque sera strictement
isolee derriere un adaptateur interne : aucune API tierce ne fuira vers les
couches applicatives ou les phases suivantes. Le protocole `MarkdownParser`
reste le point d'injection pour substituer un adaptateur sans impacter les
phases aval.

**Bibliotheques retenues :**

| Usage | Bibliotheque | Justification |
|---|---|---|
| Frontmatter YAML | `PyYAML` | Standard de facto, stable, couvre tout YAML 1.1 |
| Frontmatter TOML | `tomlkit` | Supporte TOML 1.0, preserve le style, API simple |
| Parsing Markdown | `markdown-it-py` | CommonMark-compliant, tokens structures, activement maintenu |

**Principe d'isolation :**  
Chaque bibliotheque est encapsulee dans un adaptateur prive
(`_yaml_adapter`, `_toml_adapter`, `_markdown_adapter`). Le reste du code
scribpy ne consomme jamais directement PyYAML, tomlkit ou markdown-it-py —
uniquement les types internes (`dict[str, Any]`, `MarkdownAst`). Ce couplage
minimal permet de remplacer une bibliotheque sans modifier les phases 4+.

---

## Perimetre Fonctionnel

### Inclus

- `scribpy.parser`
  - `parse_frontmatter` avec support YAML (`---`) et TOML (`+++`) ;
  - `parse_markdown` via adaptateur `markdown-it-py` ;
  - adaptateurs prives isoles : `_yaml_adapter`, `_toml_adapter`, `_markdown_adapter` ;
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
  - detection du bloc `---` (YAML) ou `+++` (TOML) en tete de fichier ;
  - parsing YAML complet via `PyYAML` (adaptateur isole) ;
  - parsing TOML complet via `tomlkit` (adaptateur isole) ;
  - diagnostic en cas de bloc non ferme ou erreur de parsing.

- CLI et core
  - exposition minimale pour verifier que le parsing fonctionne de bout en bout,
    soit via une commande dediee `scribpy parse check`, soit via une facade
    `core.parse_project_documents` appelee par les tests.

- Tests
  - frontmatter absent, YAML valide, TOML valide, blocs invalides ;
  - extraction de titres et ancres ;
  - extraction de liens internes, liens externes et images ;
  - parsing multi-fichiers dans l'ordre du `DocumentIndex` ;
  - diagnostics pour fichier illisible ou erreur de parsing.

### Exclus

- lint documentaire (`LINT001`, `LINT002`, `LINT003`, etc.) ;
- resolution effective des liens internes entre documents ;
- validation d'existence des assets ;
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
  implementation complete ;
- paquet de compatibilite `scribpy.parsers`, marque deprecie ;
- `ParseResult` dans `model.results` avec `documents`, `diagnostics` et `failed` ✓ ;
- `parse_frontmatter` minimal (regex MVP) dans `scribpy.parser.frontmatter` — a remplacer.

A creer ou completer :

- adaptateur prive `_yaml_adapter` encapsulant PyYAML ;
- adaptateur prive `_toml_adapter` encapsulant tomlkit ;
- adaptateur prive `_markdown_adapter` encapsulant markdown-it-py ;
- reimplementation de `parse_frontmatter` via les adaptateurs (supprimer le regex MVP) ;
- implementation de `parse_markdown` via `_markdown_adapter` ;
- fonctions `extract_headings`, `extract_links`, `extract_assets` ;
- fonction `parse_document_file` ;
- fonction `parse_documents` ;
- tests unitaires et tests de chaine avec un projet temporaire.

---

## Plan de Realisation

### Etape 1 — Resultat de parsing ✓ TERMINE

Objectif : definir le contrat retourne aux couches applicatives.

Realise dans `scribpy.model.results` :

- `ParseResult` immuable (`frozen=True`) avec :
  - `documents: tuple[Document, ...]` ;
  - `diagnostics: tuple[Diagnostic, ...]` ;
  - `failed: bool`.
- coherent avec `LintResult` et `BuildResult` existants.

Diagnostics attendus (codes reserves, pas encore tous emis) :

- `PRS001` : fichier source illisible ;
- `PRS002` : frontmatter invalide (bloc non ferme, erreur YAML/TOML) ;
- `PRS003` : erreur de parsing Markdown ;
- `PRS004` : extraction semantique incomplete ou incoherente.

### Etape 2 — Adaptateurs de frontmatter

Objectif : separer les metadonnees du contenu Markdown avec robustesse.

Etat : `parse_frontmatter` MVP (regex) present — a remplacer integralement.

A faire :

- supprimer le parser regex dans `scribpy.parser.frontmatter` ;
- creer `_yaml_adapter` : fonction privee appelant `yaml.safe_load`,
  convertissant `yaml.YAMLError` en `Diagnostic(code="PRS002")` ;
- creer `_toml_adapter` : fonction privee appelant `tomlkit.loads`,
  convertissant `tomlkit.TOMLKitError` en `Diagnostic(code="PRS002")` ;
- reimplementer `parse_frontmatter` :
  - detecter uniquement le bloc en tout debut de fichier ;
  - dispatcher vers `_yaml_adapter` si delimiteur `---`, vers `_toml_adapter`
    si delimiteur `+++` ;
  - accepter l'absence de frontmatter sans diagnostic ;
  - retourner `frontmatter`, `body` et `body_start_line` preserves ;
- mettre a jour `FrontmatterResult.frontmatter` de `dict[str, str]`
  vers `dict[str, Any]` pour couvrir listes, entiers et booleans YAML/TOML ;
- mettre a jour les tests : cas YAML simple, YAML avec types natifs, TOML,
  erreur YAML, erreur TOML, bloc non ferme, absence de frontmatter.

Contraintes :

- les adaptateurs sont prives (`_yaml_adapter`, `_toml_adapter`) et non
  importables hors de `scribpy.parser` ;
- aucun type PyYAML ou tomlkit ne doit apparaitre dans les signatures publiques ;
- ajouter `PyYAML` et `tomlkit` aux dependances de production dans
  `pyproject.toml`.

### Etape 3 — Adaptateur Markdown et parser par defaut

Objectif : produire un `MarkdownAst` exploitable par les extracteurs.

A faire :

- creer `_markdown_adapter` encapsulant `markdown-it-py` :
  - instancier `MarkdownIt` en mode CommonMark ;
  - convertir les tokens markdown-it en tokens internes scribpy
    (heading, paragraph, link, image, fenced_code) ;
  - conserver `backend="markdown-it-py"` dans le `MarkdownAst` produit ;
- implementer `parse_markdown(body, parser)` utilisant l'adaptateur par defaut
  si aucun parser n'est injecte ;
- ne pas exposer `MarkdownIt` ni ses types dans les signatures publiques.

### Etape 4 — Extraction semantique

Objectif : remplir les collections semantiques du `Document`.

A faire :

- extraire les `Heading` avec niveau, titre, ancre et ligne ;
- normaliser les ancres de maniere deterministe (compatible GitHub) ;
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

- tester les adaptateurs isoles (YAML valide, TOML valide, erreurs) ;
- tester les fonctions d'extraction de facon isolee ;
- tester un document complet avec frontmatter YAML, TOML, titres, liens et images ;
- tester plusieurs fichiers ordonnes par index ;
- tester les diagnostics d'erreur utilisateur ;
- lancer `make check`.

---

## Criteres de Sortie

La phase 3 est terminee lorsque :

- un ensemble de `SourceFile` indexe peut etre parse en `Document[]` ;
- le frontmatter YAML et TOML est extrait ou diagnostique ;
- les titres ATX sont extraits avec niveau, ligne et ancre stable ;
- les liens Markdown inline sont extraits comme `Reference` ;
- les images Markdown inline sont extraites comme `AssetRef` ;
- les erreurs de lecture, frontmatter et parsing sont retournees en
  diagnostics ;
- l'ordre des documents respecte le `DocumentIndex` ;
- aucun type PyYAML, tomlkit ou markdown-it-py n'apparait dans les API publiques ;
- l'API de parsing est utilisable par la future phase 4 de lint ;
- les tests couvrent les cas nominaux et les principaux echecs utilisateur ;
- `make check` passe.

---

## Consequences

Consequences positives :

- la phase 4 pourra implementer les regles de lint sur un modele semantique
  stable et conforme CommonMark ;
- les phases de transformation et build n'auront pas a relire ou reparcourir
  les sources brutes ;
- le parser externe reste substituable grace au protocole existant ;
- Scribpy gagne une separation claire entre lecture, parsing et validation
  documentaire ;
- les cas YAML complexes (listes, types, multilignes) sont couverts sans
  parser maison fragile.

Compromis :

- trois dependances de production ajoutees (`PyYAML`, `tomlkit`, `markdown-it-py`) ;
- les adaptateurs prives doivent etre maintenus si les APIs tierces evoluent ;
- certaines validations utiles, comme les liens casses ou assets manquants,
  resteront hors perimetre jusqu'a la phase 4 ou 9.

Risques :

- une mise a jour majeure d'une bibliotheque peut casser un adaptateur ;
- les numeros de ligne peuvent devenir faux si le frontmatter est retire sans
  compensation ;
- l'ancrage des titres peut ne pas correspondre aux conventions de tous les
  renderers.

Mitigations :

- epingler les versions majeures dans `pyproject.toml` ;
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
3. Convention d'ancres a adopter par defaut : GitHub-compatible (retenu).
4. Niveau de severite pour un frontmatter invalide : erreur bloquante ou warning
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
   - adaptateurs `_yaml_adapter` et `_toml_adapter` ;
   - reimplementation de `parse_frontmatter` ;
   - tests dedies (YAML, TOML, absent, invalide).

2. `markdown-parser-adapter`
   - adaptateur `_markdown_adapter` encapsulant `markdown-it-py` ;
   - implementation de `parse_markdown` ;
   - tokens heading/link/image/fenced_code ;
   - tests de l'adaptateur.

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
