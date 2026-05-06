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
        """Return UTF-8 text content from ``path``."""

    def write_text(self, path: Path, content: str) -> None:
        """Write UTF-8 text content to ``path``."""

    def exists(self, path: Path) -> bool:
        """Return whether ``path`` exists."""

    def glob(self, root: Path, pattern: str) -> Iterable[Path]:
        """Yield paths below ``root`` matching ``pattern``."""


@runtime_checkable
class MarkdownParser(Protocol):
    """Markdown parser adapter."""

    def parse(self, source: str) -> MarkdownAst:
        """Parse Markdown source into a parser-neutral AST."""


@runtime_checkable
class HtmlRenderer(Protocol):
    """HTML renderer adapter."""

    def render(self, document: object, css_files: Sequence[Path]) -> str:
        """Render an assembled document and CSS files to HTML."""


@runtime_checkable
class PdfRenderer(Protocol):
    """PDF renderer adapter."""

    def render(self, html: str, css_files: Sequence[Path], output_path: Path) -> None:
        """Render HTML and CSS files to ``output_path``."""


@runtime_checkable
class DiagramRenderer(Protocol):
    """Diagram renderer adapter."""

    def render(self, source: str, output_format: str) -> bytes:
        """Render diagram source to bytes in ``output_format``."""


__all__ = [
    "DiagramRenderer",
    "FileSystem",
    "HtmlRenderer",
    "MarkdownParser",
    "PdfRenderer",
]
