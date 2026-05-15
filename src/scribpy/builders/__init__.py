"""Output generation layer for Scribpy."""

from scribpy.builders.markdown import (
    MARKDOWN_OUTPUT_PATH,
    AssembledDocument,
    merge_documents,
    write_markdown_artifact,
)

__all__ = [
    "AssembledDocument",
    "MARKDOWN_OUTPUT_PATH",
    "merge_documents",
    "write_markdown_artifact",
]
