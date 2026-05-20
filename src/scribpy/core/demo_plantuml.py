"""PlantUML examples embedded in the valid demo project."""

from __future__ import annotations


def pipeline_plantuml() -> str:
    """Return the demo sequence diagram.

    Returns:
        Markdown section containing a PlantUML sequence diagram.
    """
    return """

## Pipeline Sequence

```plantuml
@startuml
title Scribpy HTML build pipeline
autonumber
actor Author
participant "CLI" as CLI
participant "Project Pipeline" as Pipeline
participant "Lint Engine" as Lint
participant "Transform Pipeline" as Transform
participant "PlantUML Renderer" as UML
participant "HTML Builder" as Builder

Author -> CLI: scribpy build html
CLI -> Pipeline: load config + scan files
Pipeline -> Pipeline: parse Markdown documents
Pipeline -> Lint: validate structure and assets
Lint --> Pipeline: diagnostics
alt diagnostics contain errors
  Pipeline --> CLI: blocked build
else project is valid
  Pipeline -> Transform: prepare target documents
  Transform -> UML: render fenced plantuml blocks
  UML --> Transform: local SVG assets
  Transform --> Builder: rewritten documents
  Builder --> CLI: HTML artifacts
end
CLI --> Author: deterministic build result
@enduml
```
"""


def data_model_plantuml() -> str:
    """Return the demo class diagram.

    Returns:
        Markdown section containing a PlantUML class diagram.
    """
    return """

## Semantic Model

```plantuml
@startuml
title Core document model
skinparam classAttributeIconSize 0

class ProjectConfig {
  +project_name: str
  +source_path: Path
}
class DocumentIndex {
  +entries: tuple[IndexEntry, ...]
}
class Document {
  +relative_path: Path
  +title: str
  +headings: tuple[Heading, ...]
}
class Heading {
  +level: int
  +title: str
  +anchor: str
}
class TransformedDocument {
  +content: str
}
class BuildResult {
  +success: bool
  +artifacts: tuple[BuildArtifact, ...]
}
class BuildArtifact {
  +path: Path
  +artifact_type: str
}

ProjectConfig "1" --> "1" DocumentIndex
DocumentIndex "1" o-- "*" Document
Document "1" *-- "*" Heading
Document "1" --> "1" TransformedDocument
TransformedDocument "*" --> "1" BuildResult
BuildResult "1" *-- "*" BuildArtifact
@enduml
```
"""


def deployment_plantuml() -> str:
    """Return the demo deployment/component diagram.

    Returns:
        Markdown section containing a PlantUML deployment diagram.
    """
    return """

## Offline Rendering Architecture

```plantuml
@startuml
title Offline PlantUML rendering in Scribpy
skinparam componentStyle rectangle

node "Developer workstation" {
  folder "Markdown sources" as Sources
  component "Scribpy" as Scribpy
  component "Bundled PlantUML MIT JAR" as Jar
  component "Local JVM" as JVM
  folder "Generated HTML" as HTML
  folder "Generated SVG assets" as SVG
}

cloud "External PlantUML server" as Remote

Sources --> Scribpy : fenced plantuml blocks
Scribpy --> Jar : local render request
Jar --> JVM : executes inside
Jar --> SVG : writes SVG
Scribpy --> HTML : rewrites local image links
Scribpy -[#red,dashed]x Remote : no network call
@enduml
```
"""


__all__ = ["data_model_plantuml", "deployment_plantuml", "pipeline_plantuml"]
