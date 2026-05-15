"""Target-ready document data produced by transforms."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scribpy.model.document import Document
from scribpy.parser.frontmatter import parse_frontmatter


@dataclass(frozen=True)
class TransformedDocument:
    """A document prepared for one build target.

    Attributes:
        relative_path: Source-relative document path.
        content: Target-ready Markdown content without source frontmatter.
        source_document: Parsed source document that produced this value.
    """

    relative_path: Path
    content: str
    source_document: Document

    @classmethod
    def from_document(cls, document: Document) -> TransformedDocument:
        """Create a target-ready value from a parsed source document.

        Args:
            document: Parsed source document.

        Returns:
            Transformed document containing the Markdown body only.
        """
        body = parse_frontmatter(document.source, path=document.path).body
        return cls(
            relative_path=document.relative_path,
            content=body,
            source_document=document,
        )


__all__ = ["TransformedDocument"]
