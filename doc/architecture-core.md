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
    +diagnose(rules): CollectionDiagnosticReport
    +concatenate(): MarkdownDocument
  }

  class HeadingNormalizer {
    +normalize_markdown_headings(content, base_level): str
  }

  class CollectionDiagnosticReport {
    +diagnostics: tuple[CollectionDiagnostic, ...]
    +has_errors: bool
    +by_severity(severity): tuple[CollectionDiagnostic, ...]
    +summary(): str
  }

  class CollectionDiagnostic {
    +code: str
    +severity: DiagnosticSeverity
    +message: str
    +path: Path | None
    +line: int | None
  }

  interface CollectionDiagnosticRule {
    +diagnose(context): Iterable[CollectionDiagnostic]
  }

  package "diagnostics" {
    class SourceFirstHeadingH1Rule
    class SourceH1CountRule
    class HeadingLevelOverflowRule
    class LocalImageMissingRule
    class ExternalImageReferenceRule
    class InternalMarkdownLinkRule
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
MarkdownCollection ..> HeadingNormalizer : shifts headings
MarkdownCollection ..> CollectionDiagnosticReport : returns
CollectionDiagnosticReport "1" o-- "*" CollectionDiagnostic
CollectionDiagnosticRule <|.. SourceFirstHeadingH1Rule
CollectionDiagnosticRule <|.. SourceH1CountRule
CollectionDiagnosticRule <|.. HeadingLevelOverflowRule
CollectionDiagnosticRule <|.. LocalImageMissingRule
CollectionDiagnosticRule <|.. ExternalImageReferenceRule
CollectionDiagnosticRule <|.. InternalMarkdownLinkRule
SourceFirstHeadingH1Rule ..> HeadingNormalizer : reads headings
SourceH1CountRule ..> HeadingNormalizer : reads headings
HeadingLevelOverflowRule ..> HeadingNormalizer : reads headings
LocalImageMissingRule ..> MarkdownDocument : reads image references
ExternalImageReferenceRule ..> MarkdownDocument : reads image references
InternalMarkdownLinkRule ..> MarkdownFile : reads Markdown links
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
participant "Diagnostic rules" as Rules
participant "CollectionDiagnosticReport" as Report
participant "MarkdownFile" as File
participant "FolderManifest" as Folder
participant "HeadingNormalizer" as Headings
participant "MarkdownDocument" as Document

User -> Collection : from_tree(root)
Collection -> Collection : read root scribpy.yml
Collection -> Collection : read folder scribpy.yml files
Collection -> File : from_path(path) in manifest/alphabetical order
File --> Collection : files
User -> Collection : concatenate()
Collection -> Rules : diagnose(root, files)
Rules -> Report : create diagnostics
Report --> Collection
alt report has errors
  Collection --> User : InvalidMarkdownError(report.summary())
else report has no errors
Collection -> Collection : create one H1 from project.title or root name
loop for each folder entered
  Collection -> Folder : read title or folder name
  Folder --> Collection : heading title
  Collection -> Collection : add folder heading
end
loop for each Markdown file
  Collection -> Headings : normalize_markdown_headings(content, base_level)
  Headings --> Collection : shifted content
end
Collection -> Document : MarkdownDocument(normalized content)
Document --> Collection
Collection --> User : document
end
@enduml
```

La concatenation produit un document Markdown structure pour publication :

- le document final contient un seul titre de niveau 1 ;
- ce titre vient de `project.title` dans le `scribpy.yml` racine, ou du nom du
  dossier racine si la metadonnee est absente ;
- chaque dossier traverse ajoute un titre intermediaire, avec le `title` du
  `scribpy.yml` local quand il existe, sinon le nom du dossier ;
- le titre `#` d'un fichier racine devient `##`, le titre `#` d'un fichier dans
  un sous-dossier devient `###`, et ainsi de suite ;
- les titres situes dans les blocs de code fenced ne sont pas modifies, grace au
  scanner de lignes fourni par `mkforge`.

## Flux de diagnostic collection

```plantuml
@startuml
actor User
participant "MarkdownCollection" as Collection
participant "Diagnostic registry" as Registry
participant "CollectionDiagnosticRule" as Rule
participant "CollectionDiagnosticReport" as Report

User -> Collection : diagnose()
Collection -> Registry : default rules
Registry --> Collection : SourceFirstHeadingH1Rule
Registry --> Collection : SourceH1CountRule
Registry --> Collection : HeadingLevelOverflowRule
Registry --> Collection : LocalImageMissingRule
Registry --> Collection : ExternalImageReferenceRule
Registry --> Collection : InternalMarkdownLinkRule
loop for each rule
  Collection -> Rule : diagnose(context)
  Rule --> Collection : diagnostics
end
Collection -> Report : CollectionDiagnosticReport(diagnostics)
Report --> Collection
Collection --> User : report
@enduml
```

Les diagnostics de collection appliquent le pattern Strategy : chaque controle
est une regle independante qui implemente `CollectionDiagnosticRule`. Le registre
par defaut contient aujourd'hui :

- `SourceFirstHeadingH1Rule`, qui verifie que le premier titre Markdown de
  chaque fichier source est un H1 ;
- `SourceH1CountRule`, qui verifie que chaque fichier source contient
  exactement un titre H1 ;
- `HeadingLevelOverflowRule`, qui detecte les titres qui depasseraient le
  niveau 6 apres insertion du H1 racine et des titres de dossiers.
- `LocalImageMissingRule`, qui signale en erreur les images locales dont le
  fichier n'existe pas, en resolvant les chemins relatifs depuis le fichier
  Markdown source ;
- `ExternalImageReferenceRule`, qui signale en warning les images externes sans
  effectuer de requete reseau dans le noyau deterministe.
- `InternalMarkdownLinkRule`, qui signale en erreur les liens vers fichiers
  Markdown inexistants ou les liens Markdown qui sortent de la racine de
  collection. Les URL externes, les ancres seules et les liens non Markdown sont
  ignores par cette regle.

De nouveaux controles, comme les images absentes ou les liens casses, peuvent
etre ajoutes par nouvelle regle sans modifier le moteur. Chaque regle concrete
vit dans son propre module sous `scribpy.core.diagnostics.rules` afin d'eviter
un fichier central difficile a maintenir.

`MarkdownCollection.concatenate()` bloque seulement sur les diagnostics de
severite `ERROR`. Les diagnostics de severite `WARNING`, par exemple les images
externes, restent consultables avec `collection.diagnose()` mais ne bloquent pas
l'assemblage.

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
manifeste. Les diagnostics de collection appliquent Strategy et Registry :
`MarkdownCollection` depend d'une interface de regle, et le registre par defaut
permet d'ajouter des controles sans etendre une grande condition centrale.
