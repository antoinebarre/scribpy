# Scribpy Core Architecture

## Objectif

Scribpy repart d'un noyau simple : un fichier Markdown est l'objet metier
central quand on manipule le disque, et un document Markdown est l'objet metier
central quand on manipule du contenu en memoire. Les fonctions Markdown
generiques ne sont pas reecrites dans Scribpy : elles sont deleguees a
`mkforge` quand le package les expose.

## Principes

- `MarkdownFile` represente un fichier Markdown physique avec son chemin.
- `MarkdownDocument` represente du contenu Markdown en memoire, sans chemin.
- `MarkdownImageReference` represente une image ecrite dans le Markdown, pas
  encore un fichier resolu sur disque.
- `MarkdownCollection` represente une liste ordonnee de fichiers Markdown
  chargee depuis une arborescence.
- Les modifications retournent une nouvelle instance pour faciliter les tests
  et eviter les effets de bord.
- `mkforge` est l'adaptateur de verification et validation Markdown.
- Les rendus HTML, site et qualite multi-fichiers resteront des services
  separes pour eviter que les objets Markdown deviennent des objets qui font
  tout.

## Limite volontaire

`MarkdownDocument` extrait les references d'images, mais ne controle pas que les
fichiers existent. Cette verification demande un contexte disque. Elle restera
donc dans `MarkdownFile` ou dans un futur service de qualite documentaire.

## Vue statique

```plantuml
@startuml
skinparam classAttributeIconSize 0

package "scribpy.core" {
  class MarkdownDocument {
    +content: str
    +image_references: tuple[MarkdownImageReference, ...]
    +with_content(content): MarkdownDocument
    +replace_text(old, new): MarkdownDocument
  }

  class MarkdownFile {
    +path: Path
    +content: str
    +encoding: str
    +from_path(path, encoding): MarkdownFile
    +with_content(content): MarkdownFile
    +replace_text(old, new): MarkdownFile
    +to_document(): MarkdownDocument
    +write(path): Path
    +verify(settings, custom_rules): VerificationReport
    +has_valid_images(timeout): bool
    +has_expected_headings(expected, strict): bool
    +has_expected_yaml(expected, strict): bool
  }

  class MarkdownImageReference {
    +alt_text: str
    +target: str
    +title: str | None
    +line: int | None
    +column: int | None
  }

  class MarkdownCollection {
    +root: Path
    +files: tuple[MarkdownFile, ...]
    +manifest: RootManifest
    +from_tree(root, encoding): MarkdownCollection
    +concatenate(): MarkdownDocument
  }

  class RootManifest {
    +project: dict[str, object]
    +build: dict[str, object]
    +order: tuple[str, ...]
  }

  class FolderManifest {
    +title: str | None
    +order: tuple[str, ...]
  }
}

package "mkforge" {
  class VerificationReport
  class VerificationSettings
  interface MarkdownRule
}

MarkdownFile ..> VerificationReport : returns
MarkdownFile ..> VerificationSettings : accepts
MarkdownFile ..> MarkdownRule : accepts
MarkdownFile ..> mkforge : delegates validation
MarkdownFile ..> MarkdownDocument : creates
MarkdownDocument "1" o-- "*" MarkdownImageReference
MarkdownCollection "1" o-- "*" MarkdownFile
MarkdownCollection "1" o-- "1" RootManifest
MarkdownCollection ..> MarkdownDocument : concatenates
MarkdownCollection ..> FolderManifest : reads local order
@enduml
```

## Ordre des fichiers

`MarkdownCollection.from_tree()` parcourt recursivement les dossiers et
sous-dossiers, garde les fichiers `.md` et `.markdown`, puis applique les
manifests `scribpy.yml` quand ils existent.

Le `scribpy.yml` racine est le seul manifeste riche. Il peut contenir les
metadonnees du projet, les reglages globaux et l'ordre des enfants directs de la
racine :

```yaml
project:
  title: Guide utilisateur
build:
  toc: true
  renumber_headings: false
order:
  - intro.md
  - architecture/
```

Les `scribpy.yml` de dossier sont locaux et limites a `title` et `order` :

```yaml
title: Architecture
order:
  - contexte.md
  - decisions.md
```

Chaque manifeste controle uniquement les enfants directs de son dossier :

```text
docs/
  scribpy.yml
  intro.md
  architecture/
    scribpy.yml
    contexte.md
    decisions.md
```

Si un dossier n'a pas de `scribpy.yml`, ses enfants directs sont parcourus par
ordre alphabetique. Si un dossier definit des reglages globaux comme `build`,
ils produisent un `ScribpyManifestWarning` et sont ignores. Si un manifeste
liste un enfant inexistant ou un chemin profond comme `guide/install.md`, une
erreur `InvalidScribpyManifestError` est levee.

## Flux d'extraction des images

```plantuml
@startuml
actor User
participant "MarkdownDocument" as Document
participant "mkforge line scanner" as Scanner
participant "MarkdownImageReference" as Image

User -> Document : MarkdownDocument(content)
Document -> Scanner : lines_outside_fenced_code(content)
Scanner --> Document : lines
Document -> Image : create for each image reference
Image --> Document
Document --> User : image_references
@enduml
```

## Flux de verification fichier

```plantuml
@startuml
actor User
participant "MarkdownFile" as File
participant "mkforge" as Mkforge
participant "VerificationReport" as Report

User -> File : verify()
File -> Mkforge : verify_markdown(content, source_path)
Mkforge -> Report : create diagnostics
Report --> Mkforge
Mkforge --> File : report
File --> User : report
@enduml
```

## Flux de concatenation v1

```plantuml
@startuml
actor User
participant "MarkdownCollection" as Collection
participant "MarkdownFile" as File
participant "MarkdownDocument" as Document

User -> Collection : from_tree(root)
Collection -> Collection : read root scribpy.yml
Collection -> Collection : read folder scribpy.yml files
Collection -> File : from_path(path) in manifest/alphabetical order
File --> Collection : files
User -> Collection : concatenate()
Collection -> Document : MarkdownDocument(joined content)
Document --> Collection
Collection --> User : document
@enduml
```

## Extension prevue

Les futurs rendus utiliseront le pattern Strategy afin d'ajouter HTML, MkDocs
ou d'autres sorties sans modifier les objets Markdown de base.

```plantuml
@startuml
skinparam classAttributeIconSize 0

class MarkdownDocument
class MarkdownCollection

interface MarkdownRenderer {
  +render(document): RenderResult
}

class HtmlRenderer
class MkDocsSiteRenderer

MarkdownRenderer <|.. HtmlRenderer
MarkdownRenderer <|.. MkDocsSiteRenderer
HtmlRenderer ..> MarkdownDocument
MkDocsSiteRenderer ..> MarkdownCollection
@enduml
```

## Decision de conception

Le premier design pattern applique est l'adaptateur : `MarkdownFile` expose une
API metier stable pour Scribpy et delegue les controles Markdown a `mkforge`.
`MarkdownDocument` applique une approche de prototype immuable : chaque
modification retourne un nouveau document avec ses references derivees
recalculees. `MarkdownCollection` applique une strategie d'ordre simple en v1
basee sur `scribpy.yml`, avec repli alphabetique lorsqu'un dossier n'a pas de
manifeste.
