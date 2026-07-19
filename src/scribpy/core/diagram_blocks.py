"""Shared Markdown diagram block rendering."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path, PurePosixPath
from typing import Protocol

from scribpy.core.manifest import BuildSettings
from scribpy.core.mermaid.renderer import (
    make_renderer as make_mermaid_renderer,
)
from scribpy.core.plantuml.renderer import (
    make_renderer as make_plantuml_renderer,
)

_PLANTUML_BLOCK = re.compile(
    r"^```plantuml\n(?P<diagram>.*?)^```",
    re.DOTALL | re.MULTILINE | re.IGNORECASE,
)
_MERMAID_BLOCK = re.compile(
    r"^```mermaid\n(?P<diagram>.*?)^```",
    re.DOTALL | re.MULTILINE | re.IGNORECASE,
)


class _DiagramRenderer(Protocol):
    """Render diagram source into PNG bytes."""

    def render(self, diagram: str) -> bytes:
        """Render one diagram.

        Args:
            diagram: Diagram source without fenced delimiters.

        Returns:
            Rendered PNG bytes.
        """
        ...


def render_diagram_blocks(
    content: str,
    build: BuildSettings,
    generated_dir: Path,
    reference_prefix: str = "assets/generated",
) -> str:
    """Render PlantUML and Mermaid blocks using project build settings.

    Args:
        content: Markdown containing diagram blocks.
        build: Build settings loaded from the root project manifest.
        generated_dir: Directory receiving generated PNG files.
        reference_prefix: POSIX path written before generated filenames.

    Returns:
        Markdown with diagram blocks replaced by image references.

    Raises:
        ValueError: If a configured renderer backend is unknown.
        PlantUmlRenderError: If PlantUML rendering fails.
        MermaidRenderError: If Mermaid rendering fails.
        NotImplementedError: If a configured backend is not implemented.
        OSError: If a generated image cannot be written.
    """
    plantuml_renderer = make_plantuml_renderer(
        build.plantuml_backend,
        server_url=build.plantuml_server_url,
    )
    mermaid_renderer = make_mermaid_renderer(
        build.mermaid_backend,
        command=build.mermaid_command,
    )
    rendered = _render_blocks(
        content,
        _PLANTUML_BLOCK,
        plantuml_renderer,
        generated_dir,
        reference_prefix,
    )
    return _render_blocks(
        rendered,
        _MERMAID_BLOCK,
        mermaid_renderer,
        generated_dir,
        reference_prefix,
    )


def png_filename(diagram: str) -> str:
    """Derive a stable PNG filename from diagram source.

    Args:
        diagram: Diagram source text.

    Returns:
        SHA-256 based PNG filename.
    """
    digest = hashlib.sha256(diagram.encode("utf-8")).hexdigest()
    return f"{digest}.png"


def _render_blocks(
    content: str,
    pattern: re.Pattern[str],
    renderer: _DiagramRenderer,
    generated_dir: Path,
    reference_prefix: str,
) -> str:
    """Replace matching diagram blocks with stored PNG references.

    Args:
        content: Markdown containing diagram blocks.
        pattern: Compiled fenced-block pattern for one language.
        renderer: Renderer used for matching blocks.
        generated_dir: Directory receiving generated PNG files.
        reference_prefix: POSIX path written before generated filenames.

    Returns:
        Markdown with matching blocks replaced by image references.
    """
    generated_dir.mkdir(parents=True, exist_ok=True)

    def _replace(match: re.Match[str]) -> str:
        """Render and replace one matched diagram block.

        Args:
            match: Diagram block regular-expression match.

        Returns:
            Markdown image reference for the rendered diagram.
        """
        diagram = match.group("diagram")
        filename = png_filename(diagram)
        destination = generated_dir / filename
        if not destination.exists():
            destination.write_bytes(renderer.render(diagram))
        reference = PurePosixPath(reference_prefix) / filename
        return f"![diagram]({reference})"

    return pattern.sub(_replace, content)


__all__ = ["render_diagram_blocks"]
