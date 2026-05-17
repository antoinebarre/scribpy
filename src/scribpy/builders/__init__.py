"""Output generation layer for Scribpy."""

from scribpy.builders.html_single_page import (
    build_single_page_html,
    render_markdown_to_html,
    write_single_page_artifact,
)
from scribpy.builders.html_site import (
    build_mkdocs_yaml,
    run_mkdocs_build,
    write_site_artifacts,
    write_site_artifacts_with_css,
)
from scribpy.builders.markdown import (
    MARKDOWN_OUTPUT_PATH,
    AssembledDocument,
    merge_documents,
    write_markdown_artifact,
)

__all__ = [
    "AssembledDocument",
    "MARKDOWN_OUTPUT_PATH",
    "build_mkdocs_yaml",
    "build_single_page_html",
    "merge_documents",
    "render_markdown_to_html",
    "run_mkdocs_build",
    "write_markdown_artifact",
    "write_single_page_artifact",
    "write_site_artifacts",
    "write_site_artifacts_with_css",
]
