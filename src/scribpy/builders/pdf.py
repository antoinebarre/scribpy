"""PDF document model, default CSS, and renderer adapter."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any, cast

from scribpy.model import BuildArtifact, Diagnostic

PDF_OUTPUT_DIR = Path("build/pdf")
PDF_OUTPUT_FILE = "document.pdf"

DEFAULT_PDF_CSS = """\
body {
  color: #111827;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 10.5pt;
  line-height: 1.45;
}

h1, h2, h3 {
  color: #172554;
  break-after: avoid;
}

pre, blockquote, table, img {
  break-inside: avoid;
}

img {
  display: block;
  height: auto;
  margin: 12pt auto;
  max-height: 650pt;
  max-width: 100%;
  object-fit: contain;
  page-break-inside: avoid;
}

p:has(> img:only-child) {
  margin: 12pt 0;
  text-align: center;
}

table {
  border-collapse: collapse;
  width: 100%;
}

th, td {
  border: 0.5pt solid #cbd5e1;
  padding: 4pt 6pt;
}
"""


@dataclass(frozen=True)
class PdfOptions:
    """Renderer-neutral PDF options.

    Attributes:
        paper_size: Page size forwarded to adapters that support it.
        toc_level: Deepest heading level included in PDF bookmarks.
    """

    paper_size: str = "A4"
    toc_level: int = 3


@dataclass(frozen=True)
class PdfDocument:
    """Markdown payload prepared for an injected PDF renderer.

    Attributes:
        markdown: Fully assembled Markdown payload.
        root: Filesystem root used to resolve Markdown assets.
        css_files: User CSS files already resolved to absolute paths.
        default_css: Built-in printable CSS applied before user CSS.
        options: Renderer-neutral PDF options.
    """

    markdown: str
    root: Path
    css_files: tuple[Path, ...]
    default_css: str
    options: PdfOptions


@dataclass(frozen=True)
class PdfRenderResult:
    """Result returned by injected PDF renderers.

    Attributes:
        artifact: PDF artifact on success.
        diagnostics: Diagnostics emitted by the renderer.
    """

    artifact: BuildArtifact | None
    diagnostics: tuple[Diagnostic, ...] = ()

    @property
    def success(self) -> bool:
        """Return whether rendering produced an artifact without errors.

        Returns:
            Whether rendering succeeded.
        """
        return self.artifact is not None and not any(
            diagnostic.severity == "error" for diagnostic in self.diagnostics
        )


class MarkdownPdfRenderer:
    """Optional ``markdown-pdf`` adapter used by the default PDF build."""

    def render(
        self, document: PdfDocument, output_path: Path
    ) -> PdfRenderResult:
        """Render a prepared PDF document using ``markdown-pdf``.

        Args:
            document: Prepared PDF document payload.
            output_path: Destination PDF path.

        Returns:
            PDF render result containing an artifact or diagnostics.
        """
        markdown_pdf = _load_markdown_pdf()
        if markdown_pdf is None:
            return PdfRenderResult(
                artifact=None,
                diagnostics=(
                    Diagnostic(
                        severity="error",
                        code="PDF001",
                        message="PDF renderer dependency markdown-pdf is not installed.",
                        hint="Install optional PDF support with: pip install scribpy[pdf]",
                    ),
                ),
            )
        markdown_pdf_cls = markdown_pdf["MarkdownPdf"]
        section_cls = markdown_pdf["Section"]

        css_text, diagnostics = read_pdf_css(document)
        if diagnostics:
            return PdfRenderResult(artifact=None, diagnostics=diagnostics)

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            pdf = markdown_pdf_cls(
                toc_level=document.options.toc_level,
                optimize=True,
            )
            section = section_cls(
                document.markdown,
                root=str(document.root),
                paper_size=document.options.paper_size,
            )
            pdf.add_section(section, user_css=css_text)
            pdf.save(str(output_path))
        except Exception as exc:
            return PdfRenderResult(
                artifact=None,
                diagnostics=(
                    Diagnostic(
                        severity="error",
                        code="PDF002",
                        message=f"PDF rendering failed: {exc}",
                        path=output_path,
                        hint="Check the PDF CSS, image paths, and renderer options.",
                    ),
                ),
            )

        return PdfRenderResult(
            artifact=BuildArtifact(
                path=output_path,
                target="pdf",
                artifact_type="document",
                metadata={"renderer": "markdown-pdf"},
            )
        )


def read_pdf_css(
    document: PdfDocument,
) -> tuple[str, tuple[Diagnostic, ...]]:
    """Read default and user PDF CSS as one CSS string.

    Args:
        document: Prepared PDF document with resolved CSS paths.

    Returns:
        CSS text and diagnostics raised while reading user CSS files.
    """
    parts = [document.default_css]
    diagnostics: list[Diagnostic] = []
    for css_file in document.css_files:
        try:
            parts.append(css_file.read_text(encoding="utf-8"))
        except OSError as exc:
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="PDF003",
                    message=f"Cannot read PDF CSS file: {exc}",
                    path=css_file,
                    hint="Check that the CSS path exists and is readable.",
                )
            )
    return "\n\n".join(parts), tuple(diagnostics)


def _load_markdown_pdf() -> dict[str, Any] | None:
    """Load the optional ``markdown_pdf`` module.

    Returns:
        Imported classes needed by the adapter, or ``None`` when unavailable.
    """
    try:
        module = import_module("markdown_pdf")
    except ImportError:
        return None
    return {
        "MarkdownPdf": cast(Any, module).MarkdownPdf,
        "Section": cast(Any, module).Section,
    }


__all__ = [
    "DEFAULT_PDF_CSS",
    "PDF_OUTPUT_DIR",
    "PDF_OUTPUT_FILE",
    "MarkdownPdfRenderer",
    "PdfDocument",
    "PdfOptions",
    "PdfRenderResult",
    "read_pdf_css",
]
