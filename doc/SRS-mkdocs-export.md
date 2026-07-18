# SRS — Export MkDocs

## Exigences

- **REQ-MKDOCS-01** — Scribpy SHALL exposer la fonction publique
  `mkdocs_export(source: Path, output: Path) -> None` pour exporter un projet
  Scribpy sous forme d'arborescence statique compatible avec MkDocs.
  - Critère d'acceptation : un appel valide crée `output/mkdocs.yml` et
    `output/docs/` sans importer le package Python `mkdocs`.
- **REQ-MKDOCS-02** — L'export SHALL charger le projet avec
  `MarkdownCollection.from_tree(source)`.
  - Critère d'acceptation : les fichiers exportés et leur ordre sont ceux de
    la collection régie par les manifestes `scribpy.yml`.
- **REQ-MKDOCS-03** — L'export SHALL copier chaque fichier Markdown de la
  collection sous `output/docs/` en préservant son chemin relatif à `source`.
  - Critère d'acceptation : `source/architecture/contexte.md` est écrit dans
    `output/docs/architecture/contexte.md`.
- **REQ-MKDOCS-04** — L'export SHALL rendre chaque bloc `plantuml` en PNG avec
  le backend `build.plantuml_backend` et chaque bloc `mermaid` en PNG avec le
  backend `build.mermaid_backend` du manifeste racine.
  - Critère d'acceptation : la fonction partagée de rendu reçoit le
    `BuildSettings` chargé depuis `scribpy.yml`, transmet les backends
    configurés aux factories `make_renderer` correspondantes et remplace les
    blocs par des références d'image dans les fichiers Markdown exportés.
- **REQ-MKDOCS-05** — L'export SHALL écrire les diagrammes rendus dans
  `output/docs/assets/generated/` sous un nom `<sha256>.png` dérivé de leur
  source.
  - Critère d'acceptation : deux blocs identiques d'un même langage partagent
    le même fichier PNG et une référence correcte depuis chaque document.
- **REQ-MKDOCS-06** — L'export SHALL copier les images locales référencées par
  les sources Markdown dans `output/docs/assets/` et SHALL réécrire chaque
  référence relativement au fichier Markdown exporté.
  - Critère d'acceptation : une image utilisée par un document imbriqué est
    accessible depuis ce document, les images externes restent inchangées et
    deux images locales homonymes ne s'écrasent pas.
- **REQ-MKDOCS-07** — L'export SHALL conserver sans modification les liens
  Markdown internes vers d'autres fichiers `.md`.
  - Critère d'acceptation : `[API](../api/reference.md)` reste identique dans
    le fichier exporté.
- **REQ-MKDOCS-08** — L'export SHALL conserver les titres Markdown sources et
  SHALL ignorer `build.heading_numbering`.
  - Critère d'acceptation : aucun préfixe de numérotation n'est ajouté aux
    headings, que le réglage soit activé ou non.
- **REQ-MKDOCS-09** — `mkdocs.yml` SHALL contenir `site_name` issu de
  `RootManifest.project["title"]`, `docs_dir: docs` et une clé `nav`.
  - Critère d'acceptation : le YAML généré est chargeable avec
    `yaml.safe_load` et expose exactement ces valeurs de configuration.
- **REQ-MKDOCS-10** — La navigation SHALL reproduire l'ordre et la hiérarchie
  des manifestes pour tous les fichiers Markdown exportés.
  - Critère d'acceptation : chaque feuille apparaît une fois à son chemin
    POSIX relatif à `docs/`, sous les groupes correspondant à ses dossiers,
    dans l'ordre de parcours de la collection.
- **REQ-MKDOCS-11** — Le libellé d'une feuille de navigation SHALL être le
  texte de son premier H1 source.
  - Critère d'acceptation : un fichier commençant par `# Référence` produit
    l'entrée `Référence: <chemin>.md` sans modifier le fichier source.
- **REQ-MKDOCS-12** — Le libellé d'un groupe SHALL être
  `FolderManifest.title` lorsqu'il est renseigné, sinon le nom du dossier
  capitalisé.
  - Critère d'acceptation : un dossier `architecture` sans titre manifeste
    produit le groupe `Architecture`.
- **REQ-MKDOCS-13** — L'export SHALL lever `ScaffoldCollisionError` avant toute
  écriture lorsque `output/mkdocs.yml` existe déjà.
  - Critère d'acceptation : le fichier existant et le contenu de `output/`
    restent inchangés après l'exception.
- **REQ-MKDOCS-14** — Le module `scribpy.core.mkdocs` SHALL rester indépendant
  de `scribpy.core.assembly` et de tout moteur de template.
  - Critère d'acceptation : aucun module sous `scribpy.core.mkdocs` n'importe
    `scribpy.core.assembly`, `mkdocs` ou un package de templating.
- **REQ-MKDOCS-15** — Le merge Markdown et l'export MkDocs SHALL importer et
  appeler la même fonction publique de rendu des diagrammes, pilotée par les
  options `RootManifest.build` issues du manifeste du projet.
  - Critère d'acceptation : les deux orchestrateurs importent
    `scribpy.core.diagram_blocks.render_diagram_blocks`, lui transmettent le
    même type `BuildSettings`, et aucune fonction de rendu spécifique à l'un
    des deux workflows n'existe.
