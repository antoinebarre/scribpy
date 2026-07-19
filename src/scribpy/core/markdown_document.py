"""Markdown document domain object."""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass, field

from mkforge import MarkdownSource
from mkforge.verification.source_scan import lines_outside_fenced_code

from scribpy.core.markdown_image import MarkdownImageReference

_IMAGE_REFERENCE = re.compile(
    r"!\[(?P<alt_text>[^\]]*)]\((?P<body>[^)\n]+)\)",
)


@dataclass(frozen=True, slots=True)
class MarkdownDocument:
    """Represent Markdown source as an in-memory document.

    Attributes:
        content: Markdown source text.
        image_references: Image references found in the Markdown source.
    """

    content: str
    image_references: tuple[MarkdownImageReference, ...] = field(init=False)

    def __post_init__(self) -> None:
        """Extract derived Markdown references after initialization."""
        object.__setattr__(
            self,
            "image_references",
            _extract_image_references(self.content),
        )

    def with_content(self, content: str) -> MarkdownDocument:
        """Return a copy with replaced Markdown source text.

        Args:
            content: Replacement Markdown source text.

        Returns:
            Markdown document object with refreshed image references.
        """
        return MarkdownDocument(content)

    def replace_text(self, old: str, new: str) -> MarkdownDocument:
        """Return a copy with text occurrences replaced.

        Args:
            old: Existing text to replace.
            new: Replacement text.

        Returns:
            Markdown document object with updated content.
        """
        return self.with_content(self.content.replace(old, new))


def _extract_image_references(
    content: str,
) -> tuple[MarkdownImageReference, ...]:
    """Extract inline image references from Markdown source.

    Args:
        content: Markdown source text to scan.

    Returns:
        Image references found outside fenced code blocks.
    """
    source = MarkdownSource.from_text(content)
    references: list[MarkdownImageReference] = []
    for line in lines_outside_fenced_code(source):
        for match in _IMAGE_REFERENCE.finditer(line.text):
            target, title = _split_image_body(match.group("body"))
            references.append(
                MarkdownImageReference(
                    alt_text=match.group("alt_text"),
                    target=target,
                    title=title,
                    line=line.number,
                    column=match.start() + 1,
                ),
            )
    return tuple(references)


def _split_image_body(body: str) -> tuple[str, str | None]:
    """Split a Markdown image body into target and optional title.

    Args:
        body: Text between Markdown image parentheses.

    Returns:
        Image target and optional image title.
    """
    parts = _body_parts(body)
    if not parts:
        return "", None
    title = " ".join(parts[1:]) or None
    return parts[0], title


def _body_parts(body: str) -> tuple[str, ...]:
    """Return shell-like parts from a Markdown image body.

    Args:
        body: Text between Markdown image parentheses.

    Returns:
        Parsed body parts with surrounding quotes removed.
    """
    try:
        return tuple(shlex.split(body.strip()))
    except ValueError:
        return tuple(body.strip().split())
