"""Large Mermaid diagrams used by the generated demo project."""


def delivery_flow_mermaid() -> str:
    """Return a demo Mermaid delivery flowchart.

    Returns:
        Markdown section containing a Mermaid flowchart.
    """
    return """

## Delivery Control Flow

```mermaid
flowchart LR
  author[Author commits Markdown] --> checks{Quality gate}
  checks -->|index| index[Index check]
  checks -->|parse| parse[Semantic parse]
  checks -->|lint| lint[Lint rules]
  index --> decision{Blocking diagnostics?}
  parse --> decision
  lint --> decision
  decision -->|yes| fix[Fix source documents]
  fix --> author
  decision -->|no| build{Build target}
  build --> markdown[Markdown manual]
  build --> single[Single-page HTML]
  build --> site[MkDocs site]
  single --> assets[Copy CSS and assets]
  site --> mkdocs[Materialize MkDocs project]
  assets --> publish[Publish artifact]
  mkdocs --> publish
  markdown --> publish
```
"""


def extension_architecture_mermaid() -> str:
    """Return a demo Mermaid class diagram for extension architecture.

    Returns:
        Markdown section containing a Mermaid class diagram.
    """
    return """

## Extension Registry Model

```mermaid
classDiagram
  class ExtensionRegistry {
    +tuple lint_rules
    +tuple markdown_transforms
    +tuple html_transforms
    +tuple code_block_plugins
    +with_lint_rule(rule)
    +with_markdown_transform(transform)
    +with_code_block_plugin(plugin)
  }
  class CodeBlockPlugin {
    <<protocol>>
    +language
    +has_blocks(content)
    +preflight()
    +render_documents(documents)
  }
  class PlantUmlPlugin {
    +language = plantuml
    +preflight()
    +render_documents(documents)
  }
  class MermaidPlugin {
    +language = mermaid
    +preflight()
    +render_documents(documents)
  }
  class HtmlBuilder {
    +build_single_page()
    +build_site()
  }
  ExtensionRegistry o-- CodeBlockPlugin
  CodeBlockPlugin <|.. PlantUmlPlugin
  CodeBlockPlugin <|.. MermaidPlugin
  HtmlBuilder --> ExtensionRegistry
```
"""


def ci_timeline_mermaid() -> str:
    """Return a demo Mermaid sequence diagram for CI execution.

    Returns:
        Markdown section containing a Mermaid sequence diagram.
    """
    return """

## CI Execution Timeline

```mermaid
sequenceDiagram
  autonumber
  participant Dev as Developer
  participant CI as CI Runner
  participant S as Scribpy CLI
  participant P as Project Pipeline
  participant R as Render Plugins
  participant A as Artifacts

  Dev->>CI: push branch
  CI->>S: scribpy index check
  S->>P: resolve config and scan docs
  P-->>S: indexed documents
  CI->>S: scribpy parse check
  S->>P: parse Markdown semantics
  P-->>S: documents and diagnostics
  CI->>S: scribpy lint
  S->>P: run lint rules
  P-->>S: lint result
  alt no blocking diagnostics
    CI->>S: scribpy build html --mode site
    S->>R: render supported code blocks
    R-->>S: SVG diagram assets
    S->>A: write MkDocs inputs and site
  else blocking diagnostics
    S-->>CI: fail with formatted diagnostics
  end
```
"""


__all__ = [
    "ci_timeline_mermaid",
    "delivery_flow_mermaid",
    "extension_architecture_mermaid",
]
