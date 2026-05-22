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
    MARKDOWN_OUTPUT_DIR,
    AssembledDocument,
    merge_documents,
    write_markdown_artifact,
)
from scribpy.builders.pdf import (
    DEFAULT_PDF_CSS,
    PDF_OUTPUT_DIR,
    MarkdownPdfRenderer,
    PdfDocument,
    PdfOptions,
    PdfRenderResult,
    read_pdf_css,
)

__all__ = [
    "AssembledDocument",
    "MARKDOWN_OUTPUT_DIR",
    "PDF_OUTPUT_DIR",
    "DEFAULT_PDF_CSS",
    "MarkdownPdfRenderer",
    "PdfDocument",
    "PdfOptions",
    "PdfRenderResult",
    "build_mkdocs_yaml",
    "build_single_page_html",
    "merge_documents",
    "render_markdown_to_html",
    "run_mkdocs_build",
    "write_markdown_artifact",
    "write_single_page_artifact",
    "write_site_artifacts",
    "write_site_artifacts_with_css",
    "read_pdf_css",
]
