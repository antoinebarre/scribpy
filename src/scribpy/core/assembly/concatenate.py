"""Concatenation pipeline entry point for Markdown collections."""

from __future__ import annotations

import logging
from pathlib import Path

from scribpy.core.assembly.heading_numbering import number_markdown_headings
from scribpy.core.assembly.image_collector import collect_images
from scribpy.core.assembly.link_rewriter import (
    build_file_slug_map,
    build_numbered_file_slug_map,
    rewrite_internal_links,
)
from scribpy.core.assembly.mermaid_transform import render_mermaid_blocks
from scribpy.core.assembly.pipeline import (
    AssembledDocument,
    apply_transforms,
)
from scribpy.core.assembly.plantuml_transform import render_plantuml_blocks
from scribpy.core.assembly.toc import generate_toc
from scribpy.core.manifest import heading_numbering_enabled
from scribpy.core.markdown_collection import MarkdownCollection
from scribpy.core.mermaid.renderer import (
    make_renderer as make_mermaid_renderer,
)
from scribpy.core.plantuml.renderer import (
    make_renderer as make_plantuml_renderer,
)

_log = logging.getLogger(__name__)


def concatenate(collection: MarkdownCollection, output: Path) -> None:
    """Assemble the collection into a single Markdown file on disk.

    The pipeline applies transforms in order:

    1. Heading numbering: when enabled by ``manifest.build``, assembled
       Markdown headings are numbered by MkForge.
    2. Internal link rewriting: ``[label](file.md)`` links are replaced by
       ``[label](#slug)`` anchors pointing to the H1 title slug of the
       target file.
    3. Table of contents: when ``manifest.build["toc"]`` is ``True``, a
       Markdown list linking to all headings below H1 is inserted after the
       first H1.  Slugs are consistent with those produced by step 2.
       ``manifest.build["toc_depth"]`` controls how many heading levels below
       H1 are included (default: 3, i.e. up to H4).
    4. PlantUML rendering: ````plantuml`` fenced blocks are rendered to PNG
       files in ``output.parent/assets/generated/`` and replaced by image
       references.  The backend is selected from
       ``manifest.build["plantuml_backend"]`` (default: ``"web"``).
    5. Mermaid rendering: ````mermaid`` fenced blocks are rendered to PNG
       files in ``output.parent/assets/generated/`` and replaced by image
       references.  The backend is selected from
       ``manifest.build["mermaid_backend"]`` (default: ``"web"``).
    6. Image collection: local images are copied to ``output.parent/assets/``
       and their references are rewritten accordingly.

    Args:
        collection: Markdown collection to assemble.
        output: Destination file path for the assembled Markdown document.

    Raises:
        PlantUmlRenderError: If the PlantUML backend fails to render a diagram.
        MermaidRenderError: If the Mermaid backend fails to render a diagram.
        NotImplementedError: If a ``local`` backend is configured.
        OSError: If the output file cannot be written.
    """
    _log.info(
        "Assembling %d file(s) from '%s' → '%s'",
        len(collection.files),
        collection.root,
        output,
    )
    raw_doc = collection.concatenate()
    assets_dir = output.parent / "assets"
    generated_dir = assets_dir / "generated"
    file_slug_map = build_file_slug_map(collection.files)

    build = collection.manifest.build
    plantuml_renderer = make_plantuml_renderer(build.plantuml_backend)
    mermaid_renderer = make_mermaid_renderer(build.mermaid_backend)
    should_number_headings = heading_numbering_enabled(collection.manifest)
    should_generate_toc = build.toc
    toc_depth = build.toc_depth

    def _number_headings(doc: AssembledDocument) -> AssembledDocument:
        return doc.with_content(number_markdown_headings(doc.content))

    def _rewrite_links(doc: AssembledDocument) -> AssembledDocument:
        slug_map = (
            build_numbered_file_slug_map(collection.files, doc.content)
            if should_number_headings
            else file_slug_map
        )
        return doc.with_content(rewrite_internal_links(doc.content, slug_map))

    def _insert_toc(doc: AssembledDocument) -> AssembledDocument:
        return doc.with_content(generate_toc(doc.content, toc_depth))

    def _render_plantuml(doc: AssembledDocument) -> AssembledDocument:
        return doc.with_content(
            render_plantuml_blocks(
                doc.content, plantuml_renderer, generated_dir
            )
        )

    def _render_mermaid(doc: AssembledDocument) -> AssembledDocument:
        return doc.with_content(
            render_mermaid_blocks(doc.content, mermaid_renderer, generated_dir)
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
    optional_numbering = (_number_headings,) if should_number_headings else ()
    optional_toc = (_insert_toc,) if should_generate_toc else ()
    final = apply_transforms(
        initial,
        (
            *optional_numbering,
            _rewrite_links,
            *optional_toc,
            _render_plantuml,
            _render_mermaid,
            _collect_images,
        ),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(final.content, encoding="utf-8")
    _log.info("Write complete: '%s' (%d chars)", output, len(final.content))
