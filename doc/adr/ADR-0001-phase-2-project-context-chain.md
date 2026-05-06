# ADR-0001 — Planification de la phase 2 : chaîne de contexte projet

**Date:** 2026-05-06  
**Statut:** proposé  
**Décideurs:** Antoine Barré  
**Références:** `doc/FUNCTIONAL_CHAINS.md`, `doc/SDD.md`

---

## Contexte

`doc/FUNCTIONAL_CHAINS.md` définit une progression par chaînes fonctionnelles.
La phase 1 stabilise les contrats partagés : modèles immuables, protocoles de
services, résultats typés et diagnostics. Le code actuel contient déjà les
premiers objets `model`, les protocoles et les utilitaires de diagnostics et de
fichiers Markdown.

La phase 2 doit maintenant rendre Scribpy capable de comprendre un projet de
documentation avant toute étape de parsing, lint ou build.

Dans `doc/FUNCTIONAL_CHAINS.md`, la phase 2 couvre :

1. FC-01 Load Project Context.
2. FC-02 Discover and Index Sources.
3. la commande CLI `scribpy index check`.

Cette phase est volontairement limitée : elle ne parse pas encore les fichiers
Markdown et ne lance pas encore de lint documentaire. Elle établit seulement le
contexte projet, la configuration, la découverte des sources et la validité de
l'index.

---

## Décision

La phase 2 sera implémentée comme une tranche verticale complète :

```text
CLI -> service applicatif -> config -> project scan -> document index -> diagnostics
```

Le livrable principal sera une capacité utilisateur observable :

```text
scribpy index check
```

Cette commande devra :

- localiser ou accepter un répertoire projet ;
- trouver et charger `scribpy.toml` ;
- valider les sections de configuration nécessaires à la découverte ;
- découvrir les fichiers Markdown de manière déterministe ;
- construire un `DocumentIndex` selon le mode configuré ;
- diagnostiquer les chemins manquants, invalides ou dupliqués ;
- retourner un code de sortie stable selon la présence d'erreurs.

La phase 2 ne doit pas introduire de dépendance externe obligatoire. Le parsing
TOML utilisera `tomllib`, disponible dans la bibliothèque standard Python 3.12.

---

## Périmètre Fonctionnel

### Inclus

- `scribpy.config`
  - recherche ascendante de `scribpy.toml` ;
  - chargement TOML ;
  - types de configuration minimaux pour la phase 2 ;
  - validation utilisateur sous forme de `Diagnostic`.

- `scribpy.project`
  - résolution du répertoire racine ;
  - scan du répertoire source ;
  - création des `SourceFile` ;
  - construction du `DocumentIndex` ;
  - validation des modes `filesystem` et `explicit`.

- `scribpy.cli`
  - sous-commandes minimales `index check` ;
  - affichage des diagnostics ;
  - codes de sortie.

- `scribpy.core`
  - façade minimale pour déclencher la vérification d'index depuis Python.

- Tests
  - chargement et validation de configuration ;
  - découverte déterministe des fichiers ;
  - index explicite valide ;
  - diagnostics pour fichiers manquants, doublons et chemins sortant du projet ;
  - comportement CLI.

### Exclus

- parsing Markdown ;
- extraction des titres, liens et assets ;
- règles de lint documentaire ;
- génération d'artefacts ;
- modes `hybrid` avancés ;
- extensions et plugins.

---

## État Actuel

Déjà disponible :

- `Diagnostic` et types de sévérité ;
- `SourceFile`, `DocumentIndex`, `Project` ;
- protocoles `FileSystem`, `MarkdownParser`, `HtmlRenderer`, `PdfRenderer`,
  `DiagramRenderer` ;
- `LintResult`, `BuildResult`, `BuildArtifact` ;
- utilitaires `list_md_files`, `read_md_file`, `write_md_file` ;
- tests de base sur les modèles et utilitaires.

À créer ou compléter :

- dataclasses de configuration ;
- module TOML ;
- logique `find_config`, `load_toml_config`, `parse_config`,
  `validate_config`, `load_config` ;
- service de chargement projet ;
- scan projet utilisant les conventions de configuration ;
- validation d'index ;
- CLI réelle à la place du message actuel `Hello from scribpy!`.

---

## Plan de Réalisation

### Étape 1 — Configuration minimale

Objectif : rendre `scribpy.toml` lisible et validable.

À faire :

- créer `scribpy.config.types` avec :
  - `ProjectConfig` ;
  - `PathConfig` ;
  - `IndexConfig` ;
  - `Config`.
- définir les valeurs par défaut minimales :
  - `paths.source = "doc"` ou `"docs"` selon la convention retenue ;
  - `index.mode = "filesystem"` ;
  - `index.files = ()`.
- créer `scribpy.utils.toml` ou une fonction interne basée sur `tomllib` ;
- implémenter :
  - `find_config(start: Path) -> Path | None` ;
  - `load_toml_config(path: Path) -> dict[str, object]` ;
  - `parse_config(raw) -> Config` ;
  - `validate_config(config) -> tuple[Diagnostic, ...]` ;
  - `load_config(path) -> tuple[Config | None, tuple[Diagnostic, ...]]`.

Diagnostics attendus :

- `CFG001` : fichier `scribpy.toml` introuvable ;
- `CFG002` : TOML invalide ;
- `CFG003` : section ou valeur de configuration invalide ;
- `CFG004` : chemin configuré non autorisé ou non relatif.

### Étape 2 — Scan projet

Objectif : produire des `SourceFile` depuis le projet configuré.

À faire :

- résoudre le root projet à partir du fichier de config ;
- résoudre `paths.source` sous le root ;
- découvrir les fichiers `.md` récursivement ;
- conserver des chemins relatifs stables ;
- trier de manière déterministe ;
- retourner les diagnostics sans exception pour les erreurs utilisateur.

Diagnostics attendus :

- `PRJ001` : répertoire source manquant ;
- `PRJ002` : aucun fichier Markdown trouvé ;
- `PRJ003` : chemin source hors du projet.

### Étape 3 — Construction et validation d'index

Objectif : produire un `DocumentIndex` fiable pour les phases suivantes.

À faire :

- implémenter le mode `filesystem` avec l'ordre déterministe issu du scan ;
- implémenter le mode `explicit` avec l'ordre configuré ;
- vérifier les fichiers déclarés mais absents ;
- détecter les doublons ;
- vérifier que chaque entrée reste relative au répertoire source ou au projet ;
- garder `hybrid` hors périmètre ou le diagnostiquer comme non supporté.

Diagnostics attendus :

- `IDX001` : mode d'index inconnu ou non supporté ;
- `IDX002` : fichier explicite manquant ;
- `IDX003` : entrée dupliquée ;
- `IDX004` : entrée hors périmètre projet ;
- `IDX005` : fichier découvert mais absent de l'index explicite, en warning.

### Étape 4 — Service applicatif

Objectif : exposer une opération unique réutilisable par le CLI et `core`.

À faire :

- créer un service `run_index_check(root: Path | None, services) -> LintResult`
  ou équivalent ;
- composer :
  - recherche config ;
  - chargement config ;
  - scan projet ;
  - construction index ;
  - validation index ;
  - agrégation diagnostics ;
  - calcul de `failed`.
- garder les erreurs utilisateur sous forme de diagnostics.

### Étape 5 — CLI `scribpy index check`

Objectif : fournir la première capacité opérationnelle de la phase 2.

À faire :

- remplacer le placeholder `Hello from scribpy!` par un CLI minimal ;
- ajouter une commande `index check` ;
- accepter une option `--root` ou un argument de chemin ;
- afficher les diagnostics via `utils.diagnostics` ;
- retourner :
  - `0` si aucun diagnostic bloquant ;
  - `1` si au moins une erreur ;
  - `2` pour une erreur CLI inattendue ou mauvaise utilisation.

### Étape 6 — Tests et qualité

Objectif : verrouiller les contrats avant la phase 3.

À faire :

- ajouter des fixtures temporaires avec `scribpy.toml` ;
- tester les cas heureux `filesystem` et `explicit` ;
- tester les diagnostics attendus ;
- tester le CLI via invocation de `main` ou subprocess léger ;
- lancer `make check`.

---

## Critères de Sortie

La phase 2 est terminée lorsque :

- `scribpy.toml` est localisé, chargé et validé ;
- les fichiers sources Markdown sont découverts dans un ordre déterministe ;
- `DocumentIndex` est construit en mode `filesystem` et `explicit` ;
- les chemins invalides, absents ou dupliqués produisent des diagnostics ;
- `scribpy index check` fonctionne en local et en CI ;
- les tests couvrent les cas nominaux et les échecs utilisateur ;
- `make check` passe.

---

## Conséquences

Conséquences positives :

- les phases 3 à 8 pourront s'appuyer sur un contexte projet stable ;
- les erreurs de configuration seront détectées tôt ;
- le CLI commencera à exposer un comportement utile ;
- les futurs builders auront un ordre de documents reproductible.

Compromis :

- le périmètre reste volontairement modeste ;
- le mode `hybrid` est repoussé ;
- les dataclasses `Config` risquent d'évoluer quand lint, transforms et builders
  ajouteront leurs propres sections.

Risques :

- choisir une convention par défaut `doc` ou `docs` trop tôt peut créer une
  friction utilisateur ;
- mélanger chemins relatifs au root et chemins relatifs au source dir peut
  introduire des ambiguïtés ;
- une CLI trop riche dès maintenant pourrait ralentir la stabilisation du noyau.

Mitigations :

- documenter explicitement la base de chaque chemin ;
- garder les types immuables et les fonctions petites ;
- tester les chemins avec des sous-dossiers ;
- limiter le CLI à `index check` pour cette phase.

---

## Décisions Ouvertes

1. Convention par défaut du répertoire source : `doc` ou `docs`.
2. Forme exacte de `scribpy.toml` pour l'index explicite.
3. Niveau de sévérité pour un fichier Markdown découvert mais non listé en mode
   `explicit`.

Proposition initiale :

```toml
[project]
name = "my-docs"

[paths]
source = "doc"

[index]
mode = "filesystem"
files = []
```

Pour ce dépôt, `source = "doc"` est cohérent avec la structure actuelle.

---

## Séquence Recommandée de Pull Requests

1. `config-minimal`
   - types de configuration ;
   - loader TOML ;
   - validation de base.

2. `project-scan`
   - découverte Markdown ;
   - `SourceFile` depuis config ;
   - tests de déterminisme.

3. `document-index`
   - modes `filesystem` et `explicit` ;
   - validation d'index ;
   - diagnostics `IDX`.

4. `index-check-cli`
   - service applicatif ;
   - `core.check_index` ou équivalent ;
   - commande `scribpy index check` ;
   - tests CLI.

Cette séquence conserve une progression verticale tout en évitant de mélanger
la phase 2 avec le parsing Markdown de la phase 3.
