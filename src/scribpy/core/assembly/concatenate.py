"""Concatenation pipeline entry point for Markdown collections."""

from __future__ import annotations

from pathlib import Path

from scribpy.core.assembly.image_collector import collect_images
from scribpy.core.assembly.link_rewriter import (
    build_file_slug_map,
    rewrite_internal_links,
)
from scribpy.core.assembly.pipeline import AssembledDocument, apply_transforms
from scribpy.core.markdown_collection import MarkdownCollection


def concatenate(collection: MarkdownCollection, output: Path) -> None:
    """Assemble the collection into a single Markdown file on disk.

    The pipeline applies two transforms in order:

    1. Internal link rewriting: ``[label](file.md)`` links are replaced by
       ``[label](#slug)`` anchors pointing to the H1 title slug of the
       target file.
    2. Image collection: local images are copied to ``output.parent/assets/``
       and their references are rewritten accordingly.

    Args:
        collection: Markdown collection to assemble.
        output: Destination file path for the assembled Markdown document.

    Raises:
        InvalidMarkdownError: If collection diagnostics contain blocking
            errors.
        OSError: If the output file cannot be written.
    """
    raw_doc = collection.concatenate()
    assets_dir = output.parent / "assets"
    file_slug_map = build_file_slug_map(collection.files)

    def _rewrite_links(doc: AssembledDocument) -> AssembledDocument:
        return doc.with_content(
            rewrite_internal_links(doc.content, file_slug_map)
        )

    def _collect_images(doc: AssembledDocument) -> AssembledDocument:
        return doc.with_content(
            collect_images(doc.content, doc.source_root, assets_dir)
        )

    initial = AssembledDocument(
        content=raw_doc.content,
        source_root=collection.root,
        output=output,
    )
    final = apply_transforms(initial, (_rewrite_links, _collect_images))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(final.content, encoding="utf-8")
