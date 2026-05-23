"""PDF-specific asset preparation helpers."""

from __future__ import annotations

from dataclasses import replace
from importlib import import_module
from pathlib import Path
from typing import Any, cast

from scribpy.builders.pdf import PdfDocument
from scribpy.model import BuildArtifact, Diagnostic


def rasterize_svg_artifacts_for_pdf(
    document: PdfDocument,
    artifacts: tuple[BuildArtifact, ...],
) -> tuple[PdfDocument, tuple[BuildArtifact, ...], tuple[Diagnostic, ...]]:
    """Rasterize local SVG artifacts to PNG and rewrite Markdown references.

    Args:
        document: Prepared PDF document.
        artifacts: Local artifacts referenced by the PDF document.

    Returns:
        Updated document, generated PNG artifacts, and diagnostics.
    """
    fitz = _load_fitz()
    if fitz is None:
        return document, (), ()

    markdown = document.markdown
    raster_artifacts: list[BuildArtifact] = []
    diagnostics: list[Diagnostic] = []
    for artifact in artifacts:
        if artifact.path.suffix.lower() != ".svg":
            continue
        result = _rasterize_one_svg(fitz, document, artifact)
        if result.diagnostic is not None:
            diagnostics.append(result.diagnostic)
            continue
        if result.artifact is not None:
            raster_artifacts.append(result.artifact)
            markdown = result.markdown
    return (
        replace(document, markdown=markdown),
        tuple(raster_artifacts),
        tuple(diagnostics),
    )


class _RasterizeOneResult:
    """Internal result object for one SVG rasterization."""

    def __init__(
        self,
        *,
        markdown: str,
        artifact: BuildArtifact | None = None,
        diagnostic: Diagnostic | None = None,
    ) -> None:
        """Create a rasterization result."""
        self.markdown = markdown
        self.artifact = artifact
        self.diagnostic = diagnostic


def _rasterize_one_svg(
    fitz: Any,
    document: PdfDocument,
    artifact: BuildArtifact,
) -> _RasterizeOneResult:
    """Rasterize one SVG artifact."""
    png_path = artifact.path.with_suffix(".png")
    try:
        svg = fitz.open("svg", artifact.path.read_bytes())
        page = svg[0]
        pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        pixmap.save(png_path)
    except Exception as exc:
        return _RasterizeOneResult(
            markdown=document.markdown,
            diagnostic=Diagnostic(
                severity="error",
                code="PDF004",
                message=f"Cannot rasterize SVG for PDF: {exc}",
                path=artifact.path,
                hint="Check that the SVG is valid or provide a PNG asset.",
            ),
        )
    return _RasterizeOneResult(
        markdown=_rewrite_artifact_reference(
            document.markdown, document.root, artifact.path, png_path
        ),
        artifact=BuildArtifact(
            path=png_path,
            target="pdf",
            artifact_type=artifact.artifact_type,
            metadata={"source": str(artifact.path)},
        ),
    )


def _load_fitz() -> Any | None:
    """Load optional PyMuPDF for SVG rasterization."""
    try:
        return cast(Any, import_module("fitz"))
    except ImportError:
        return None


def _rewrite_artifact_reference(
    markdown: str,
    root: Path,
    old_path: Path,
    new_path: Path,
) -> str:
    """Rewrite one artifact path in Markdown from SVG to PNG."""
    try:
        old_ref = old_path.relative_to(root).as_posix()
        new_ref = new_path.relative_to(root).as_posix()
    except ValueError:
        old_ref = old_path.name
        new_ref = new_path.name
    return markdown.replace(f"]({old_ref})", f"]({new_ref})")


__all__ = ["rasterize_svg_artifacts_for_pdf"]
