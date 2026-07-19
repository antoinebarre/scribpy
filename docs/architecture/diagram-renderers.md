# Diagram renderers

PlantUML and Mermaid each expose a narrow renderer `Protocol` with one
`render(diagram: str) -> bytes` method, and each has its own `make_renderer()`
factory that maps a backend name from `scribpy.yml` to a concrete
implementation. The two diagram types are otherwise independent packages —
`scribpy.core.plantuml` and `scribpy.core.mermaid` — that happen to share the
same architecture and the same diagram-encoding helper.

```plantuml
@startuml
skinparam classAttributeIconSize 0

package "scribpy.core.plantuml" {
  interface PlantUmlRenderer {
    +render(diagram: str): bytes
  }
  class "make_renderer(backend, server_url)" as puml_factory
  class PlantUmlServerRenderer {
    +server_url: str
    +render(diagram: str): bytes
  }
  class KrokiRenderer as puml_kroki {
    +render(diagram: str): bytes
  }
  class LocalRenderer as puml_local {
    +render(diagram: str): bytes
  }
}

package "scribpy.core.mermaid" {
  interface MermaidRenderer {
    +render(diagram: str): bytes
  }
  class "make_renderer(backend, command)" as mmid_factory
  class KrokiRenderer as mmid_kroki {
    +render(diagram: str): bytes
  }
  class MermaidCliRenderer as mmid_cli {
    +command: str
    +render(diagram: str): bytes
  }
  class LocalRenderer as mmid_local
}

package "scribpy.core" {
  class "diagram_encoding.encode_diagram()" as encoder
  class "kroki_http.kroki_render()" as kroki_http
}

PlantUmlRenderer <|.. PlantUmlServerRenderer
PlantUmlRenderer <|.. puml_kroki
PlantUmlRenderer <|.. puml_local
puml_factory ..> PlantUmlRenderer : instantiates
puml_kroki ..> kroki_http : uses
kroki_http ..> encoder : uses

MermaidRenderer <|.. mmid_kroki
MermaidRenderer <|.. mmid_cli
mmid_local ..> mmid_cli : is a compatibility alias of
mmid_factory ..> MermaidRenderer : instantiates
mmid_kroki ..> kroki_http : uses

note right of puml_local
  Placeholder only:
  render() always raises
  NotImplementedError
end note
@enduml
```

!!! note "Same simple name, different packages"
    Both packages define a class literally called `KrokiRenderer`
    (`scribpy.core.plantuml.kroki.KrokiRenderer` and
    `scribpy.core.mermaid.kroki.KrokiRenderer`). They are unrelated classes
    that happen to share a name and a Kroki-calling strategy — always refer to
    them by their fully qualified module path, not the bare class name.

## Why this design

Both diagram types use the same three-layer shape — `Protocol`, `make_renderer()`
factory, one module per backend — which is the Strategy + Registry pattern
applied twice. The engine (`render_diagram_blocks()` in
`scribpy.core.diagram_blocks`, see [Assembly pipeline](assembly-pipeline.md))
never branches on backend name; it only calls `make_renderer(backend_name,
...)` and then `.render(diagram)`. Adding a new backend — a self-hosted Kroki
instance, a different PlantUML deployment — means writing one new class that
satisfies the `Protocol` and registering it in that package's `_BACKENDS`
dict; no existing renderer class or the pipeline itself needs to change.

`diagram_encoding.encode_diagram()` is deliberately generic: it knows zlib
compression (level 9) and URL-safe base64 encoding, and nothing about HTTP,
Kroki, or PlantUML. `kroki_http.kroki_render()` is the one place that knows
Kroki's URL shape (`https://kroki.io/<language>/png/<encoded>`), its
timeout, and its User-Agent header — both `plantuml.kroki.KrokiRenderer` and
`mermaid.kroki.KrokiRenderer` call into it with their own `language` string
and domain exception class. This isolation means a future non-Kroki web
backend does not have to touch the encoding module, and the encoding module
can be tested with zero network mocking.

## Backend selection

| Diagram type | `scribpy.yml` key | Backend name | Class | Default |
|---|---|---|---|---|
| PlantUML | `build.plantuml_backend` | `plantuml_server` | `scribpy.core.plantuml.server.PlantUmlServerRenderer` | yes |
| PlantUML | `build.plantuml_backend` | `kroki`, `web` (alias) | `scribpy.core.plantuml.kroki.KrokiRenderer` | no |
| PlantUML | `build.plantuml_backend` | `local` | `scribpy.core.plantuml.local.LocalRenderer` | no — raises `NotImplementedError` |
| Mermaid | `build.mermaid_backend` | `kroki`, `web` (alias) | `scribpy.core.mermaid.kroki.KrokiRenderer` | yes |
| Mermaid | `build.mermaid_backend` | `mermaid_cli`, `local` (alias) | `scribpy.core.mermaid.cli.MermaidCliRenderer` | no |

PlantUML defaults to `plantuml_server`, using `build.plantuml_server_url`
(default `https://www.plantuml.com/plantuml`). `PlantUmlServerRenderer`
encodes the UTF-8 diagram source with PlantUML's own hexadecimal `~h`
encoding (not the Kroki zlib+base64url scheme) and calls
`<server_url>/png/<encoded>`; the same class serves both the public server
and self-hosted PlantUML Server instances.

Mermaid defaults to `kroki`. The optional `mermaid_cli` backend (aliased as
`local`) calls the executable named by `build.mermaid_command` (default
`mmdc`) — the official `@mermaid-js/mermaid-cli` tool, which must be
installed separately with Node.js. Each render runs in an isolated temporary
directory with an argument list built without a shell
(`asyncio.create_subprocess_exec`), and is bounded by a 60-second timeout.

PlantUML's `local` backend exists only so the factory and manifest validation
can reference the name `"local"` without error; `LocalRenderer.render()`
unconditionally raises `NotImplementedError` telling the caller to use
`kroki` or `plantuml_server` instead. A real local-JAR implementation is
future work.

## Example

```python
from scribpy.core.plantuml.renderer import make_renderer as make_plantuml_renderer
from scribpy.core.mermaid.renderer import make_renderer as make_mermaid_renderer

plantuml_renderer = make_plantuml_renderer(
    "plantuml_server",
    server_url="https://www.plantuml.com/plantuml",
)
png_bytes = plantuml_renderer.render("@startuml\nA -> B\n@enduml")

mermaid_renderer = make_mermaid_renderer("kroki")
png_bytes = mermaid_renderer.render("graph TD; A-->B;")
```

Both factories raise `ValueError` for an unknown backend name, listing the
known backends in the error message.
