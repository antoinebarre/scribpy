"""Demonstrate Scribpy core Markdown features.

The demo builds a realistic multi-chapter technical documentation project
under ``work/demo/input`` and assembles it into a single Markdown file under
``work/demo/output``.  It exercises the full pipeline:

- Multi-level folder hierarchy with local manifests
- Internal Markdown link rewriting (file.md -> #slug)
- Local image collection (PNG/SVG -> assets/)
- PlantUML diagram rendering (fenced blocks -> assets/generated/)
- Collection diagnostics (heading rules, image rules, link rules)
- File-level validation helpers
"""

from __future__ import annotations

import shutil
import sys
import warnings
from pathlib import Path

DEMO_ROOT = Path("work/demo")
INPUT_ROOT = DEMO_ROOT / "input"
OUTPUT_ROOT = DEMO_ROOT / "output"
REPOSITORY_ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = REPOSITORY_ROOT / "src"

_EXCERPT_LINES = 40

_FAKE_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
    b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
    b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


_ROOT_MANIFEST = """\
project:
  title: Projet Alpha — Documentation Technique
  version: 2.1.0
  author: Equipe Architecture
build:
  plantuml_backend: web
  toc: true
order:
  - 01-intro.md
  - 02-quickstart.md
  - architecture/
  - api/
  - operations/
"""

_INTRO = """\
# Introduction

Bienvenue dans la documentation du **Projet Alpha**.

Ce document couvre l'architecture, l'API et les operations.

## Perimetre

Le projet Alpha est un service de traitement de donnees distribue.
Il expose une API REST et s'integre avec plusieurs systemes tiers.

## Navigation rapide

- [Demarrage rapide](02-quickstart.md)
- [Architecture](architecture/01-overview.md)
- [API Reference](api/01-endpoints.md)
- [Operations](operations/01-deploy.md)

![Logo Projet Alpha](assets/logo.svg)
"""

_QUICKSTART = """\
# Demarrage rapide

## Prerequis

- Python 3.11+
- Docker 24+
- PostgreSQL 15+

## Installation

```bash
pip install project-alpha
docker compose up -d
```

## Premier appel API

```python
import alpha
client = alpha.Client(base_url='http://localhost:8080')
result = client.process(payload={'data': [1, 2, 3]})
print(result.status)
```

Voir [Architecture](architecture/01-overview.md) pour comprendre le flux.
"""

_ARCH_MANIFEST = """\
title: Architecture
order:
  - 01-overview.md
  - 02-components.md
  - 03-data-flow.md
"""

_ARCH_OVERVIEW = """\
# Vue d'ensemble

Le systeme Alpha est compose de trois couches principales.

![Diagramme d'architecture](../assets/architecture.png)

## Couches

| Couche | Role |
|--------|------|
| API Gateway | Routage et authentification |
| Processing Engine | Transformation des donnees |
| Storage Layer | Persistance et cache |

Voir [Composants](02-components.md) pour les details.

```plantuml
@startuml
skinparam componentStyle rectangle
package "Projet Alpha" {
  [API Gateway] --> [Processing Engine]
  [Processing Engine] --> [Storage Layer]
  [Processing Engine] --> [Message Queue]
}
@enduml
```
"""

_ARCH_COMPONENTS = """\
# Composants

## API Gateway

Le gateway expose les endpoints REST et gere l'authentification JWT.

```plantuml
@startuml
actor Client
participant "API Gateway" as GW
participant "Auth Service" as Auth
participant "Processing Engine" as PE
Client -> GW : POST /process
GW -> Auth : validate_token()
Auth --> GW : ok
GW -> PE : dispatch(payload)
PE --> GW : result
GW --> Client : 200 OK
@enduml
```

## Processing Engine

Le moteur de traitement applique les transformations via un pipeline.

```plantuml
@startuml
skinparam classAttributeIconSize 0
class Pipeline {
  +stages: list[Stage]
  +run(payload): Result
}
interface Stage {
  +process(data): data
}
class ValidationStage
class TransformStage
class OutputStage
Pipeline o-- Stage
Stage <|.. ValidationStage
Stage <|.. TransformStage
Stage <|.. OutputStage
@enduml
```

Voir [Flux de donnees](03-data-flow.md).
"""

_ARCH_DATAFLOW = """\
# Flux de donnees

## Flux nominal

```plantuml
@startuml
start
:Reception requete;
:Validation payload;
if (payload valide ?) then (oui)
  :Transformation;
  :Persistance;
  :Reponse 200;
else (non)
  :Reponse 422;
endif
stop
@enduml
```

## Gestion des erreurs

Les erreurs transitoires declenchent un retry automatique
avec backoff exponentiel (max 3 tentatives).
"""

_API_MANIFEST = """\
title: API Reference
order:
  - 01-endpoints.md
  - 02-models.md
"""

_API_ENDPOINTS = """\
# Endpoints

## POST /process

Lance le traitement d'un payload.

**Request:**

```json
{"data": [1, 2, 3], "options": {"mode": "strict"}}
```

**Response 200:**

```json
{"status": "ok", "result": [2, 4, 6], "duration_ms": 42}
```

**Response 422:**

```json
{"error": "invalid_payload", "detail": "data must be a list"}
```

Voir [Modeles](02-models.md) pour la description complete des types.
"""

_API_MODELS = """\
# Modeles de donnees

## ProcessRequest

| Champ | Type | Requis | Description |
|-------|------|--------|-------------|
| data | list[int] | oui | Donnees a traiter |
| options | Options | non | Parametres optionnels |

## ProcessResult

| Champ | Type | Description |
|-------|------|-------------|
| status | str | `ok` ou `error` |
| result | list[int] | Donnees traitees |
| duration_ms | int | Duree de traitement |

```plantuml
@startuml
skinparam classAttributeIconSize 0
class ProcessRequest {
  +data: list[int]
  +options: Options | None
}
class ProcessResult {
  +status: str
  +result: list[int]
  +duration_ms: int
}
class Options {
  +mode: str
  +timeout: int
}
ProcessRequest o-- Options
@enduml
```
"""

_OPS_MANIFEST = """\
title: Operations
order:
  - 01-deploy.md
  - 02-monitoring.md
"""

_OPS_DEPLOY = """\
# Deploiement

## Docker Compose

Le deploiement de developpement utilise Docker Compose.

```yaml
services:
  api:
    image: project-alpha:2.1.0
    ports: ['8080:8080']
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: alpha
```

## Kubernetes

```plantuml
@startuml
skinparam componentStyle rectangle
package "Kubernetes Cluster" {
  package "namespace: alpha" {
    [Deployment: api] --> [Service: api]
    [Deployment: api] --> [ConfigMap]
    [Deployment: api] --> [Secret]
  }
  [Ingress] --> [Service: api]
}
@enduml
```

Voir [Monitoring](02-monitoring.md) pour les metriques de prod.
"""

_OPS_MONITORING = """\
# Monitoring

## Metriques exposees

| Metrique | Type | Description |
|----------|------|-------------|
| `alpha_requests_total` | Counter | Nombre de requetes |
| `alpha_duration_seconds` | Histogram | Duree de traitement |
| `alpha_errors_total` | Counter | Erreurs par type |

## Alertes

- **P1** : taux d'erreur > 5 % sur 5 minutes
- **P2** : latence p99 > 2 s sur 10 minutes
- **P3** : aucune requete depuis 15 minutes (service down)

![Dashboard Grafana](../assets/dashboard.png)
"""

_LOGO_SVG = """\
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="60">
  <rect width="200" height="60" rx="8" fill="#1a1a2e"/>
  <text x="16" y="38" font-family="monospace" font-size="22" fill="#e94560">\
Alpha</text>
  <text x="90" y="38" font-family="monospace" font-size="14" fill="#aaa">\
docs</text>
</svg>
"""


def main() -> None:
    """Build the demo project and run the full Scribpy pipeline."""
    _add_source_root_to_path()
    from scribpy.core import (  # noqa: PLC0415
        MarkdownCollection,
        MarkdownFile,
        concatenate,
    )
    from scribpy.core.diagnostics import (  # noqa: PLC0415
        ExternalImageReferenceRule,
        HeadingLevelOverflowRule,
        InternalMarkdownLinkRule,
        LocalImageMissingRule,
        SourceFirstHeadingH1Rule,
        SourceH1CountRule,
    )
    from scribpy.errors import ScribpyManifestWarning  # noqa: PLC0415

    warnings.filterwarnings("ignore", category=ScribpyManifestWarning)

    _reset_demo_tree()
    _create_demo_inputs()

    sys.stdout.write("=== Scribpy Demo ===\n\n")

    collection = MarkdownCollection.from_tree(INPUT_ROOT)
    sys.stdout.write(f"Loaded {len(collection.files)} Markdown files:\n")
    for f in collection.files:
        sys.stdout.write(f"  {f.path.relative_to(INPUT_ROOT).as_posix()}\n")

    sys.stdout.write("\n--- Diagnostics ---\n")
    rules = [
        SourceFirstHeadingH1Rule(),
        SourceH1CountRule(),
        HeadingLevelOverflowRule(),
        LocalImageMissingRule(),
        ExternalImageReferenceRule(),
        InternalMarkdownLinkRule(),
    ]
    report = collection.diagnose(rules=rules)
    sys.stdout.write(f"  {report.summary()}\n")
    for diag in report.diagnostics:
        if diag.path and diag.line:
            loc = f"{diag.path.relative_to(INPUT_ROOT).as_posix()}:{diag.line}"
        elif diag.path:
            loc = diag.path.relative_to(INPUT_ROOT).as_posix()
        else:
            loc = "collection"
        sys.stdout.write(f"  [{diag.severity.name}] {loc}: {diag.message}\n")

    sys.stdout.write("\n--- Assembly (plantuml via plantuml.com) ---\n")
    output = OUTPUT_ROOT / "assembled.md"
    concatenate(collection, output)
    sys.stdout.write(f"  Output: {output}\n")
    sys.stdout.write(f"  Size: {output.stat().st_size} bytes\n")

    assets = OUTPUT_ROOT / "assets"
    images = list(assets.glob("**/*")) if assets.exists() else []
    sys.stdout.write(f"  Collected assets: {len(images)} file(s)\n")
    for img in sorted(images):
        sys.stdout.write(
            f"    {img.relative_to(OUTPUT_ROOT).as_posix()}"
            f" ({img.stat().st_size} B)\n"
        )

    sys.stdout.write(
        f"\n--- Assembled document (first {_EXCERPT_LINES} lines) ---\n"
    )
    assembled_lines = output.read_text(encoding="utf-8").splitlines()
    for line in assembled_lines[:_EXCERPT_LINES]:
        sys.stdout.write(f"  {line}\n")
    remaining = len(assembled_lines) - _EXCERPT_LINES
    if remaining > 0:
        sys.stdout.write(f"  ... ({remaining} more lines)\n")

    sys.stdout.write("\n--- File-level validation ---\n")
    intro = MarkdownFile.from_path(INPUT_ROOT / "01-intro.md")
    has_h1 = intro.has_expected_headings(((1, "Introduction"),))
    sys.stdout.write(f"  01-intro.md has H1 'Introduction': {has_h1}\n")
    arch = MarkdownFile.from_path(
        INPUT_ROOT / "architecture" / "01-overview.md"
    )
    sys.stdout.write(
        f"  architecture/01-overview.md has valid images:"
        f" {arch.has_valid_images()}\n"
    )

    sys.stdout.write(f"\nDemo complete. Outputs in: {OUTPUT_ROOT}\n")


def _create_demo_inputs() -> None:
    """Write a realistic multi-chapter technical documentation project."""
    _write_input("scribpy.yml", _ROOT_MANIFEST)
    _write_input("01-intro.md", _INTRO)
    _write_input("02-quickstart.md", _QUICKSTART)
    _write_input("architecture/scribpy.yml", _ARCH_MANIFEST)
    _write_input("architecture/01-overview.md", _ARCH_OVERVIEW)
    _write_input("architecture/02-components.md", _ARCH_COMPONENTS)
    _write_input("architecture/03-data-flow.md", _ARCH_DATAFLOW)
    _write_input("api/scribpy.yml", _API_MANIFEST)
    _write_input("api/01-endpoints.md", _API_ENDPOINTS)
    _write_input("api/02-models.md", _API_MODELS)
    _write_input("operations/scribpy.yml", _OPS_MANIFEST)
    _write_input("operations/01-deploy.md", _OPS_DEPLOY)
    _write_input("operations/02-monitoring.md", _OPS_MONITORING)
    _write_input("assets/logo.svg", _LOGO_SVG)
    _write_input("assets/architecture.png", _FAKE_PNG.decode("latin-1"))
    _write_input("assets/dashboard.png", _FAKE_PNG.decode("latin-1"))
    _write_input(
        "notes.txt",
        "Ce fichier est ignore par MarkdownCollection (extension .txt).\n",
    )


def _reset_demo_tree() -> None:
    """Reset the demo directory before writing fresh examples."""
    if DEMO_ROOT.exists():
        shutil.rmtree(DEMO_ROOT)
    INPUT_ROOT.mkdir(parents=True)
    OUTPUT_ROOT.mkdir(parents=True)


def _add_source_root_to_path() -> None:
    """Add the local ``src`` directory to Python imports for repo demos."""
    source_root = str(SOURCE_ROOT)
    if source_root not in sys.path:
        sys.path.insert(0, source_root)


def _write_input(relative_path: str, content: str) -> None:
    """Write one demo input file.

    Args:
        relative_path: File path relative to the demo input root.
        content: UTF-8 file content.
    """
    path = INPUT_ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
