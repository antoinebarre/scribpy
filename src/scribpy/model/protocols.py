"""Service protocols used to inject external capabilities into Scribpy."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from scribpy.model.markdown import MarkdownAst

if TYPE_CHECKING:
    from scribpy.builders.pdf import PdfDocument, PdfRenderResult
    from scribpy.model.diagnostic import Diagnostic
    from scribpy.model.results import BuildArtifact
    from scribpy.model.transformed import TransformedDocument


@runtime_checkable
class FileSystem(Protocol):
    """Minimal filesystem interface required by project workflows."""

    def read_text(self, path: Path) -> str:
        """Return UTF-8 text content from a path.

        Args:
            path: File path to read.

        Returns:
            UTF-8 file contents.
        """

    def write_text(self, path: Path, content: str) -> None:
        """Write UTF-8 text content to a path.

        Args:
            path: File path to write.
            content: UTF-8 text content to persist.
        """

    def exists(self, path: Path) -> bool:
        """Return whether a path exists.

        Args:
            path: Candidate filesystem path.

        Returns:
            Whether the path exists.
        """

    def glob(self, root: Path, pattern: str) -> Iterable[Path]:
        """Yield matching paths below a root.

        Args:
            root: Directory to search below.
            pattern: Glob pattern relative to ``root``.

        Returns:
            Matching paths.
        """


@runtime_checkable
class MarkdownParser(Protocol):
    """Markdown parser adapter."""

    def parse(self, source: str) -> MarkdownAst:
        """Parse Markdown source into a parser-neutral AST.

        Args:
            source: Markdown source text.

        Returns:
            Parser-neutral Markdown AST.
        """


@runtime_checkable
class HtmlRenderer(Protocol):
    """HTML renderer adapter."""

    def render(self, document: object, css_files: Sequence[Path]) -> str:
        """Render an assembled document and CSS files to HTML.

        Args:
            document: Assembled document payload to render.
            css_files: Stylesheets applied during rendering.

        Returns:
            Rendered HTML text.
        """


@runtime_checkable
class PdfRenderer(Protocol):
    """PDF renderer adapter."""

    def render(
        self, document: PdfDocument, output_path: Path
    ) -> PdfRenderResult:
        """Render a prepared PDF document to an output path.

        Args:
            document: Markdown, CSS, metadata, and options prepared by Scribpy.
            output_path: Destination PDF path.

        Returns:
            PDF render result containing an artifact or diagnostics.
        """


@runtime_checkable
class DiagramRenderer(Protocol):
    """Diagram renderer adapter."""

    def render(self, source: str, output_format: str) -> bytes:
        """Render diagram source to bytes in a target format.

        Args:
            source: Diagram source text.
            output_format: Requested diagram format.

        Returns:
            Rendered diagram bytes.
        """


@runtime_checkable
class CodeBlockPlugin(Protocol):
    """Plugin that rewrites fenced Markdown code blocks into build artifacts.

    Attributes:
        language: Markdown fence language handled by the plugin.
    """

    language: str

    def has_blocks(self, content: str) -> bool:
        """Return whether one Markdown source contains supported fenced blocks.

        Args:
            content: Markdown source text to inspect.

        Returns:
            Whether the source contains blocks handled by the plugin.
        """

    def preflight(self) -> tuple[Diagnostic, ...]:
        """Validate plugin runtime requirements before rendering begins.

        Returns:
            Diagnostics raised before rendering starts.
        """

    def render_documents(
        self,
        documents: tuple[TransformedDocument, ...],
        *,
        output_dir: Path,
        flattened: bool,
        target: str,
    ) -> tuple[
        tuple[TransformedDocument, ...],
        tuple[BuildArtifact, ...],
        tuple[Diagnostic, ...],
    ]:
        """Rewrite documents and materialize plugin artifacts.

        Args:
            documents: Target-ready documents to inspect.
            output_dir: Root directory for generated plugin assets.
            flattened: Whether output documents will be merged into one page.
            target: Artifact target label.

        Returns:
            Rewritten documents, generated artifacts, and diagnostics.
        """


__all__ = [
    "DiagramRenderer",
    "CodeBlockPlugin",
    "FileSystem",
    "HtmlRenderer",
    "MarkdownParser",
    "PdfRenderer",
]
