# Scribpy Core Architecture

## Objectif

Scribpy repart d'un noyau simple : un fichier Markdown est l'objet metier
central. Il porte son chemin, son contenu et les operations locales qui ont du
sens sur un seul fichier. Les fonctions Markdown generiques ne sont pas
reecrites dans Scribpy : elles sont deleguees a `mkforge`.

## Principes

- `MarkdownFile` represente un fichier Markdown charge ou construit en memoire.
- Les modifications retournent une nouvelle instance pour faciliter les tests
  et eviter les effets de bord.
- `mkforge` est l'adaptateur de verification et validation Markdown.
- Les rendus HTML, site et qualite multi-fichiers resteront des services
  separes pour eviter que `MarkdownFile` devienne un objet qui fait tout.

## Vue statique

```plantuml
@startuml
skinparam classAttributeIconSize 0

package "scribpy.core" {
  class MarkdownFile {
    +path: Path
    +content: str
    +encoding: str
    +from_path(path, encoding): MarkdownFile
    +with_content(content): MarkdownFile
    +replace_text(old, new): MarkdownFile
    +write(path): Path
    +verify(settings, custom_rules): VerificationReport
    +has_valid_images(timeout): bool
    +has_expected_headings(expected, strict): bool
    +has_expected_yaml(expected, strict): bool
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
@enduml
```

## Flux de verification

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

## Extension prevue

```plantuml
@startuml
skinparam classAttributeIconSize 0

class MarkdownFile

class MarkdownCollection {
  +items: tuple[MarkdownFile, ...]
  +concatenate(): MarkdownFile
  +verify_all(): CollectionReport
}

interface MarkdownRenderer {
  +render(document): RenderResult
}

class HtmlRenderer
class MkDocsSiteRenderer

MarkdownCollection "1" o-- "*" MarkdownFile
MarkdownRenderer <|.. HtmlRenderer
MarkdownRenderer <|.. MkDocsSiteRenderer
HtmlRenderer ..> MarkdownFile
MkDocsSiteRenderer ..> MarkdownCollection
@enduml
```

## Decision de conception

Le premier design pattern applique est l'adaptateur : `MarkdownFile` expose une
API metier stable pour Scribpy et delegue les controles Markdown a `mkforge`.
Les futurs rendus utiliseront le pattern Strategy afin d'ajouter HTML, MkDocs
ou d'autres sorties sans modifier l'objet Markdown de base.
