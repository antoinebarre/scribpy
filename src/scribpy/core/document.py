"""Immutable document model produced by the Markdown parser.

These dataclasses represent the intermediate structure between raw
Markdown text and the final rendered output.  They carry no rendering
logic — renderers consume them as plain data.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Heading:
    """A heading extracted from the Markdown source.

    Attributes:
        level: Heading depth (1 for ``#``, 2 for ``##``, etc.).
        text: Plain-text content of the heading (markup stripped).
        anchor: Slugified identifier suitable for in-page links.
    """

    level: int
    text: str
    anchor: str


@dataclass(frozen=True)
class ImageRef:
    """A reference to an image found in the Markdown source.

    Attributes:
        src: The ``src`` value as written in the Markdown (may be
            relative or absolute).
        alt: The alt-text, or an empty string if none was provided.
        title: The optional title attribute, or an empty string.
    """

    src: str
    alt: str = ""
    title: str = ""


@dataclass(frozen=True)
class DiagramBlock:
    """A fenced code block identified as a diagram source.

    Attributes:
        engine: Diagram engine name (e.g. ``"plantuml"``,
            ``"mermaid"``).
        source: Raw diagram source code.
        index: Zero-based position among all diagram blocks in the
            document (used as a stable identifier for error reporting).
    """

    engine: str
    source: str
    index: int


@dataclass(frozen=True)
class ParsedDocument:
    """Result of parsing a single Markdown file.

    Attributes:
        html: The full HTML body produced by the Markdown parser
            (before diagram rendering or image resolution).
        headings: Ordered list of headings found in the document.
        images: Ordered list of image references found in the document.
        diagrams: Ordered list of diagram code blocks found in the
            document.
    """

    html: str
    headings: tuple[Heading, ...] = field(default_factory=tuple)
    images: tuple[ImageRef, ...] = field(default_factory=tuple)
    diagrams: tuple[DiagramBlock, ...] = field(default_factory=tuple)
