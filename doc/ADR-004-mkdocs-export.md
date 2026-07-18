# ADR-004 — Exporter une collection Scribpy vers MkDocs

## Context

L'assemblage actuel transforme une collection en un document Markdown unique.
MkDocs attend au contraire une arborescence de sources dont les chemins et les
liens relatifs sont conservés, accompagnée d'une navigation YAML. Réutiliser le
pipeline d'assemblage appliquerait des comportements incompatibles :
concaténation, décalage ou numérotation des titres et réécriture des liens.

Les transforms de diagrammes et d'images portent une logique utile, mais les
fonctions de diagrammes actuelles appartiennent à `scribpy.core.assembly` et
certaines références qu'elles produisent supposent un document à la racine.
Les importer depuis le nouvel export violerait son autonomie ; créer une autre
API pour MkDocs ferait diverger les options, les règles de rendu et les hashes.

Un ADR `ADR-004-validation-projet.md` existe déjà. Le nom demandé pour cette
décision est conservé afin de respecter le contrat du livrable ; la
renumérotation globale des ADR est hors du périmètre de cette décision.

## Decision

Créer le package standalone `scribpy.core.mkdocs`, exposant uniquement
`mkdocs_export(source: Path, output: Path) -> None`. L'orchestrateur vérifie
d'abord l'absence de `output/mkdocs.yml`, charge une
`MarkdownCollection.from_tree(source)`, transmet son `BuildSettings` au rendu
partagé, exporte les fichiers, construit la navigation puis écrit la
configuration avec `yaml.safe_dump`.

La décomposition proposée donne une seule raison de changer à chaque module :

| Module | Responsabilité unique |
|---|---|
| `mkdocs/__init__.py` | Orchestrer l'export et exposer `mkdocs_export()` |
| `mkdocs/markdown_exporter.py` | Exporter un `MarkdownFile` à son chemin relatif et appeler les services d'assets partagés |
| `mkdocs/navigation.py` | Construire l'arbre `nav` depuis les manifestes et les premiers H1 |
| `mkdocs/configuration.py` | Sérialiser la configuration statique `mkdocs.yml` |
| `core/diagram_blocks.py` | Exposer l'unique fonction de rendu PlantUML/Mermaid, construire ses renderers depuis `BuildSettings`, dédupliquer les PNG et produire des cibles relatives |
| `core/image_collector.py` | Résoudre, copier et dédupliquer les images locales, puis produire une cible relative injectée |

`scribpy.core.diagram_blocks.render_diagram_blocks` est l'unique fonction de
rendu de blocs importée et appelée aussi bien par `concatenate()` que par
`mkdocs_export()`. Elle reçoit le `BuildSettings` du `RootManifest`, construit
les renderers avec `build.plantuml_backend` et `build.mermaid_backend`, puis
applique les deux langages. Toute nouvelle option de rendu ajoutée au YAML doit
donc entrer par `BuildSettings` et être interprétée à cet endroit unique.

Les fonctions spécifiques `assembly.render_plantuml_blocks` et
`assembly.render_mermaid_blocks` sont supprimées au profit de cet import
commun. `assembly/image_collector.py` devient seulement un re-export de
compatibilité du collecteur neutre, car la contrainte d'identité d'API porte
sur le rendu des diagrammes. Ainsi, ni l'assembly ni l'export MkDocs ne
dépendent l'un de l'autre. Les protocoles et factories PlantUML/Mermaid
existants restent les points d'adaptation des backends.

Pour chaque source Markdown, les images sont résolues depuis le dossier du
fichier source. Les cibles des images collectées et des diagrammes sont ensuite
calculées depuis le dossier du fichier exporté vers `docs/assets/` ou
`docs/assets/generated/`. Les liens qui ne sont pas des images, dont les liens
vers des fichiers `.md`, ne passent par aucune transformation. Le transform de
heading numbering n'est jamais construit.

La navigation est construite par parcours récursif des enfants directs. Le
manifeste racine pilote le premier niveau et chaque `FolderManifest` pilote son
dossier. Seuls les fichiers appartenant à la collection sont des feuilles ; un
groupe sans feuille exportée est omis. Les chemins de navigation utilisent
toujours `/`, indépendamment du système d'exploitation. Le premier H1 est lu
par un scanner qui ignore les blocs fenced. Les diagnostics existants restent
responsables de la conformité structurelle des sources.

`site_name` est la valeur textuelle de `project.title`. En son absence, le
fallback existant du domaine collection — nom du dossier source — est appliqué
afin que la configuration reste valide. La sérialisation PyYAML est retenue,
dépendance déjà utilisée pour les manifestes.

## Consequences

- L'arborescence et les liens interdocuments restent exploitables nativement
  par MkDocs.
- Le package `mkdocs` et un moteur de template ne deviennent pas des
  dépendances de Scribpy.
- Les règles d'assets deviennent réutilisables sans dépendre du type
  `AssembledDocument` ; les API publiques de l'assembly restent compatibles.
- La résolution relative par fichier corrige le cas des images utilisées dans
  des sous-dossiers, que le collecteur orienté document assemblé ne couvre pas.
- Un échec de lecture, de manifeste, de rendu ou d'écriture propage
  l'exception de domaine ou d'I/O existante. Aucune exception n'est avalée.
- Après le garde de collision, un échec de rendu ou d'I/O peut laisser des
  fichiers d'export partiels ; l'atomicité de tout un arbre n'est pas garantie.
- La coexistence de deux ADR numérotés 004 devra être résolue lors d'une
  normalisation documentaire distincte.

## Alternatives rejected

| Alternative | Raison du rejet |
|---|---|
| Appeler `concatenate()` puis exporter son résultat | Détruit la hiérarchie et réécrit titres et liens |
| Importer directement les transforms depuis `assembly/` | Crée la dépendance explicitement interdite et conserve des chemins d'assets incorrects pour les documents imbriqués |
| Conserver deux fonctions PlantUML/Mermaid ou ajouter un adaptateur MkDocs | Permet aux imports et aux options YAML de diverger selon le workflow |
| Dupliquer les transforms dans `mkdocs/` | Multiplie les implémentations des règles de hash, rendu, copie et collision |
| Introduire une interface générale `MarkdownRenderer` | Abstraction prématurée : HTML et MkDocs n'ont ni la même entrée ni le même résultat |
| Importer MkDocs pour produire sa configuration | Dépendance lourde sans besoin d'exécuter un build de site |
| Construire le YAML par template externe | Ajoute une dépendance et une couche sans logique de présentation suffisante pour la justifier |
| Aplatir les fichiers Markdown dans `docs/` | Casse les liens relatifs et perd la hiérarchie métier des manifestes |
