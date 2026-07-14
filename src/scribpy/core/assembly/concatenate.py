"""Concatenation pipeline entry point for Markdown collections."""

from __future__ import annotations

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
from scribpy.core.manifest import heading_numbering_enabled
from scribpy.core.markdown_collection import MarkdownCollection
from scribpy.core.mermaid.renderer import (
    make_renderer as make_mermaid_renderer,
)
from scribpy.core.plantuml.renderer import (
    make_renderer as make_plantuml_renderer,
)

_DEFAULT_PLANTUML_BACKEND = "web"
_DEFAULT_MERMAID_BACKEND = "web"


def concatenate(collection: MarkdownCollection, output: Path) -> None:
    """Assemble the collection into a single Markdown file on disk.

    The pipeline applies transforms in order:

    1. Heading numbering: when enabled by ``manifest.build``, assembled
       Markdown headings are numbered by MkForge.
    2. Internal link rewriting: ``[label](file.md)`` links are replaced by
       ``[label](#slug)`` anchors pointing to the H1 title slug of the
       target file.
    3. PlantUML rendering: ````plantuml`` fenced blocks are rendered to PNG
       files in ``output.parent/assets/generated/`` and replaced by image
       references.  The backend is selected from
       ``manifest.build["plantuml_backend"]`` (default: ``"web"``).
    4. Mermaid rendering: ````mermaid`` fenced blocks are rendered to PNG
       files in ``output.parent/assets/generated/`` and replaced by image
       references.  The backend is selected from
       ``manifest.build["mermaid_backend"]`` (default: ``"web"``).
    5. Image collection: local images are copied to ``output.parent/assets/``
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
    raw_doc = collection.concatenate()
    assets_dir = output.parent / "assets"
    generated_dir = assets_dir / "generated"
    file_slug_map = build_file_slug_map(collection.files)

    plantuml_backend = str(
        collection.manifest.build.get(
            "plantuml_backend", _DEFAULT_PLANTUML_BACKEND
        )
    )
    mermaid_backend = str(
        collection.manifest.build.get(
            "mermaid_backend", _DEFAULT_MERMAID_BACKEND
        )
    )
    plantuml_renderer = make_plantuml_renderer(plantuml_backend)
    mermaid_renderer = make_mermaid_renderer(mermaid_backend)
    should_number_headings = heading_numbering_enabled(collection.manifest)

    def _number_headings(doc: AssembledDocument) -> AssembledDocument:
        return doc.with_content(number_markdown_headings(doc.content))

    def _rewrite_links(doc: AssembledDocument) -> AssembledDocument:
        slug_map = (
            build_numbered_file_slug_map(collection.files, doc.content)
            if should_number_headings
            else file_slug_map
        )
        return doc.with_content(rewrite_internal_links(doc.content, slug_map))

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
    final = apply_transforms(
        initial,
        (
            *optional_numbering,
            _rewrite_links,
            _render_plantuml,
            _render_mermaid,
            _collect_images,
        ),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(final.content, encoding="utf-8")
