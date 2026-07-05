"""Concatenation pipeline entry point for Markdown collections."""

from __future__ import annotations

from pathlib import Path

from scribpy.core.assembly.image_collector import collect_images
from scribpy.core.assembly.link_rewriter import (
    build_file_slug_map,
    rewrite_internal_links,
)
from scribpy.core.assembly.mermaid_transform import render_mermaid_blocks
from scribpy.core.assembly.pipeline import AssembledDocument, apply_transforms
from scribpy.core.assembly.plantuml_transform import render_plantuml_blocks
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

    The pipeline applies four transforms in order:

    1. Internal link rewriting: ``[label](file.md)`` links are replaced by
       ``[label](#slug)`` anchors pointing to the H1 title slug of the
       target file.
    2. PlantUML rendering: ````plantuml`` fenced blocks are rendered to PNG
       files in ``output.parent/assets/generated/`` and replaced by image
       references.  The backend is selected from
       ``manifest.build["plantuml_backend"]`` (default: ``"web"``).
    3. Mermaid rendering: ````mermaid`` fenced blocks are rendered to PNG
       files in ``output.parent/assets/generated/`` and replaced by image
       references.  The backend is selected from
       ``manifest.build["mermaid_backend"]`` (default: ``"web"``).
    4. Image collection: local images are copied to ``output.parent/assets/``
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

    def _rewrite_links(doc: AssembledDocument) -> AssembledDocument:
        return doc.with_content(
            rewrite_internal_links(doc.content, file_slug_map)
        )

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
    final = apply_transforms(
        initial,
        (_rewrite_links, _render_plantuml, _render_mermaid, _collect_images),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(final.content, encoding="utf-8")
