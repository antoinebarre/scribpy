# Scribpy — Architecture Overview

![Scribpy Logo](img/logo.svg "Scribpy Logo")

Welcome to the **Scribpy** architecture documentation. This document
demonstrates the full HTML export pipeline with images, diagrams, and
table of contents.

## Technology Stack

![Python](img/python-logo.svg "Python powered")

Scribpy is built with Python 3.13+ and leverages:

- **markdown-it-py** — CommonMark-compliant Markdown parsing
- **PlantUML** — UML diagram rendering (web mode)
- **Mermaid** — Flowchart and sequence diagram rendering (web mode)

## System Architecture

The following PlantUML diagram shows the high-level architecture:

```plantuml
@startuml
skinparam style strictuml
skinparam packageStyle rectangle

package "CLI Layer" {
  [cli.py] as CLI
}

package "Pipeline" {
  [markdown_parser] as Parser
  [image_resolver] as ImgRes
  [diagram_renderer] as DiagRend
}

package "Renderers" {
  [html_renderer] as HTML
  [pdf_renderer] as PDF
}

package "Diagram Backends" {
  [plantuml_web] as PWeb
  [mermaid_web] as MWeb
}

CLI --> Parser
Parser --> ImgRes
ImgRes --> DiagRend
DiagRend --> HTML
DiagRend --> PDF
DiagRend --> PWeb
DiagRend --> MWeb
@enduml
```

## Data Flow

Here is the Mermaid representation of the data transformation pipeline:

```mermaid
flowchart LR
    A[Markdown File] --> B[Parser]
    B --> C[ParsedDocument]
    C --> D[Image Resolver]
    D --> E[Diagram Renderer]
    E --> F{Output Format}
    F -->|HTML| G[HTML File]
    F -->|PDF| H[PDF File]
```

## Module Responsibilities

| Module | Responsibility |
|--------|---------------|
| `core/markdown_parser.py` | Parse Markdown to structured document |
| `core/image_resolver.py` | Verify image existence |
| `core/diagram_renderer.py` | Dispatch rendering by engine × mode |
| `render/html_renderer.py` | Produce self-contained HTML page |
| `render/toc_widget.py` | Generate interactive TOC menu |

## Sequence Diagram — HTML Export

```plantuml
@startuml
actor User
participant CLI
participant Parser
participant ImageResolver
participant DiagramRenderer
participant HtmlRenderer

User -> CLI: scribpy export html doc.md
CLI -> Parser: parse(markdown_text)
Parser --> CLI: ParsedDocument
CLI -> ImageResolver: resolve_images(doc, base_dir)
ImageResolver --> CLI: ResolvedImages
CLI -> DiagramRenderer: render_all_diagrams(blocks, mode)
DiagramRenderer --> CLI: {index: svg_content}
CLI -> HtmlRenderer: render_html(doc, output_dir, ...)
HtmlRenderer --> CLI: Path(index.html)
CLI --> User: Done! Output in dist/
@enduml
```

## State Diagram — Render Mode Selection

```mermaid
stateDiagram-v2
    [*] --> ConfigLoaded
    ConfigLoaded --> WebMode: render_mode = "web"
    ConfigLoaded --> OfflineMode: render_mode = "offline"
    WebMode --> PlantUMLServer: plantuml block
    WebMode --> MermaidInk: mermaid block
    OfflineMode --> LocalJAR: plantuml block
    OfflineMode --> LocalMMDC: mermaid block
    PlantUMLServer --> SVGOutput
    MermaidInk --> SVGOutput
    LocalJAR --> SVGOutput
    LocalMMDC --> SVGOutput
    SVGOutput --> [*]
```

## Configuration Example

```python
from scribpy import ScribpyConfig, RenderMode, DiagramConfig

config = ScribpyConfig(
    source=Path("docs/architecture.md"),
    output_dir=Path("dist/html"),
    diagrams=DiagramConfig(render_mode=RenderMode.WEB),
)
```

## Supported Markdown Features

This section demonstrates every GFM element rendered by Scribpy.

### Text Formatting

- **Bold text** with double asterisks
- *Italic text* with single asterisks
- ~~Strikethrough~~ with double tildes
- `Inline code` with backticks
- [Hyperlinks](https://github.com) are clickable

### Lists

#### Unordered list

- First item
- Second item
  - Nested item A
  - Nested item B
- Third item

#### Ordered list

1. Parse the Markdown source
2. Resolve all image references
3. Render diagram blocks via web API
4. Generate the final HTML output

#### Task list (GFM)

- [x] Implement Markdown parser
- [x] Add image resolver
- [x] Add diagram web renderers
- [ ] Implement PDF export
- [ ] Add CLI interface

### Blockquotes

> "Simplicity is the ultimate sophistication."
> — Leonardo da Vinci

> **Note:** Scribpy handles errors gracefully.
> A missing image or a failed diagram will not stop
> the processing of other elements.

### Code Block

```bash
# Install scribpy
uv add scribpy

# Export a Markdown file to HTML
scribpy export html docs/architecture.md --css style.css --toc --output dist/
```

### Horizontal Rule

---

### Definition-style Table

| Feature | Status | Notes |
|:--------|:------:|------:|
| HTML export | ✅ Done | Single page, self-contained |
| PDF export | 🚧 Planned | Via markdown-pdf |
| PlantUML (web) | ✅ Done | Public server |
| Mermaid (web) | ✅ Done | mermaid.ink |
| PlantUML (offline) | ⏳ Pending | Requires Java |
| Mermaid (offline) | ⏳ Pending | Requires mmdc |
| TOC widget | ✅ Done | Hamburger menu |
| Custom CSS | ✅ Done | User-supplied stylesheet |

## Conclusion

Scribpy transforms Markdown into polished, self-contained HTML documents
with embedded diagrams and interactive navigation — all from a simple
command line invocation.

> Built with ❤️ in Python 3.13+
