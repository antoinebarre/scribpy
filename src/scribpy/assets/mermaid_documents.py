"""Apply Mermaid block rendering across transformed documents."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path, PurePosixPath

from scribpy.assets.mermaid_blocks import _DIAGRAMS_DIR, render_mermaid_blocks
from scribpy.logging import get_logger
from scribpy.model import BuildArtifact, Diagnostic, TransformedDocument
from scribpy.model.protocols import DiagramRenderer

logger = get_logger(__name__)


def render_mermaid_documents(
    documents: tuple[TransformedDocument, ...],
    *,
    renderer: DiagramRenderer,
    diagrams_dir: Path,
    flattened: bool,
    target: str,
) -> tuple[
    tuple[TransformedDocument, ...],
    tuple[BuildArtifact, ...],
    tuple[Diagnostic, ...],
]:
    """Render Mermaid blocks across transformed documents.

    Args:
        documents: Target-ready Markdown documents.
        renderer: Mermaid web renderer adapter.
        diagrams_dir: Absolute destination directory for generated SVGs.
        flattened: Whether all documents will be merged into one output page.
        target: Artifact target label.

    Returns:
        Rewritten documents, unique diagram artifacts, and diagnostics.
    """
    rendered_documents: list[TransformedDocument] = []
    artifacts: dict[Path, BuildArtifact] = {}
    for document in documents:
        logger.debug("Scanning %s for Mermaid blocks", document.relative_path)
        result = render_mermaid_blocks(
            document.content,
            renderer=renderer,
            output_dir=diagrams_dir,
            href_prefix=_href_prefix(document, flattened),
            target=target,
            source_label=str(document.relative_path),
        )
        if result.diagnostics:
            logger.error(
                "Mermaid rendering stopped while processing %s",
                document.relative_path,
            )
            return documents, (), result.diagnostics
        rendered_documents.append(replace(document, content=result.content))
        artifacts.update(
            {artifact.path: artifact for artifact in result.artifacts}
        )
    return tuple(rendered_documents), tuple(artifacts.values()), ()


def _href_prefix(
    document: TransformedDocument,
    flattened: bool,
) -> PurePosixPath:
    """Return the relative diagram href prefix for one output document."""
    if flattened or document.relative_path.parent == Path("."):
        return _DIAGRAMS_DIR
    depth = len(document.relative_path.parent.parts)
    return PurePosixPath(*([".."] * depth), *_DIAGRAMS_DIR.parts)


__all__ = ["render_mermaid_documents"]
