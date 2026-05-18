"""Static assets and diagram handling for scribpy."""

from scribpy.assets.copy import (
    collect_asset_paths,
    copy_assets,
    copy_css_files_single_page,
    rewrite_asset_links_single_page,
)
from scribpy.assets.plantuml import (
    JavaPlantUmlRenderer,
    PlantUmlRenderError,
    PlantUmlRenderResult,
    WebPlantUmlRenderer,
    render_plantuml_blocks,
    render_plantuml_documents,
    validate_java_plantuml_environment,
)

__all__ = [
    "collect_asset_paths",
    "copy_assets",
    "copy_css_files_single_page",
    "JavaPlantUmlRenderer",
    "PlantUmlRenderError",
    "PlantUmlRenderResult",
    "WebPlantUmlRenderer",
    "render_plantuml_blocks",
    "render_plantuml_documents",
    "validate_java_plantuml_environment",
    "rewrite_asset_links_single_page",
]
