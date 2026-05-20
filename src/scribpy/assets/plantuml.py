"""PlantUML rendering public facade."""

from __future__ import annotations

from scribpy.assets.plantuml_blocks import (
    render_plantuml_blocks,
)
from scribpy.assets.plantuml_documents import render_plantuml_documents
from scribpy.assets.plantuml_encoding import _encode6bit
from scribpy.assets.plantuml_renderers import (
    JavaPlantUmlRenderer,
    WebPlantUmlRenderer,
    validate_java_plantuml_environment,
)
from scribpy.assets.plantuml_types import (
    PlantUmlRenderError,
    PlantUmlRenderResult,
)

__all__ = [
    "JavaPlantUmlRenderer",
    "PlantUmlRenderError",
    "PlantUmlRenderResult",
    "WebPlantUmlRenderer",
    "_encode6bit",
    "render_plantuml_blocks",
    "render_plantuml_documents",
    "validate_java_plantuml_environment",
]
