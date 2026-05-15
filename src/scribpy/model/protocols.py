"""Service protocols used to inject external capabilities into Scribpy."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Protocol, runtime_checkable

from scribpy.model.markdown import MarkdownAst


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

    def render(self, html: str, css_files: Sequence[Path], output_path: Path) -> None:
        """Render HTML and CSS files to an output path.

        Args:
            html: HTML text to render.
            css_files: Stylesheets applied during rendering.
            output_path: Destination PDF path.
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


__all__ = [
    "DiagramRenderer",
    "FileSystem",
    "HtmlRenderer",
    "MarkdownParser",
    "PdfRenderer",
]
