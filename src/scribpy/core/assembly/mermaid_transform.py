"""Mermaid block rendering transform for the assembly pipeline."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from scribpy.core.mermaid.renderer import MermaidRenderer

_MERMAID_BLOCK = re.compile(
    r"^```mermaid\n(?P<diagram>.*?)^```",
    re.DOTALL | re.MULTILINE | re.IGNORECASE,
)


def render_mermaid_blocks(
    content: str,
    renderer: MermaidRenderer,
    generated_dir: Path,
) -> str:
    """Replace Mermaid fenced blocks with PNG image references.

    Each ````mermaid` block is rendered to a PNG file in *generated_dir* and
    replaced by a ``![diagram](assets/generated/<hash>.png)`` reference.
    The PNG filename is derived from the SHA-256 hash of the diagram source,
    so identical diagrams share one file and modified diagrams get a new one.

    Args:
        content: Markdown source text containing zero or more Mermaid blocks.
        renderer: Backend used to convert diagram source to PNG bytes.
        generated_dir: Directory where generated PNG files are written.

    Returns:
        Markdown source text with Mermaid blocks replaced by image references.
    """
    generated_dir.mkdir(parents=True, exist_ok=True)

    def _replace(match: re.Match[str]) -> str:
        diagram = match.group("diagram")
        png_bytes = renderer.render(diagram)
        filename = _png_filename(diagram)
        dest = generated_dir / filename
        if not dest.exists():
            dest.write_bytes(png_bytes)
        relative = f"assets/generated/{filename}"
        return f"![diagram]({relative})"

    return _MERMAID_BLOCK.sub(_replace, content)


def _png_filename(diagram: str) -> str:
    """Derive a stable PNG filename from diagram source content.

    Args:
        diagram: Mermaid diagram source text.

    Returns:
        Filename of the form ``<sha256>.png``.
    """
    digest = hashlib.sha256(diagram.encode("utf-8")).hexdigest()
    return f"{digest}.png"
