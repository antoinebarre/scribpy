"""Diagram rendering dispatch by engine and mode.

Exposes a Protocol for diagram renderers and a dispatch function
that selects the correct backend based on a composite key
``(engine, render_mode)`` (REQ-024).
"""

from __future__ import annotations

import logging
from typing import Protocol

from scribpy.config import RenderMode
from scribpy.core.document import DiagramBlock
from scribpy.errors import DiagramRenderError

_log = logging.getLogger(__name__)


class DiagramRenderer(Protocol):
    """Protocol for a diagram rendering backend.

    Each implementation renders diagram source code and returns the
    resulting SVG content as a string.
    """

    def render(self, source: str) -> str:
        """Render diagram source to SVG content.

        Args:
            source: Raw diagram source code.

        Returns:
            SVG markup as a string.

        Raises:
            DiagramRenderError: If the rendering fails.
        """
        ...


_REGISTRY: dict[tuple[str, RenderMode], DiagramRenderer] = {}


def register_renderer(
    engine: str,
    mode: RenderMode,
    renderer: DiagramRenderer,
) -> None:
    """Register a diagram renderer for a given engine and mode.

    Args:
        engine: Diagram engine name (e.g. ``"plantuml"``,
            ``"mermaid"``).
        mode: The render mode this backend handles.
        renderer: The renderer instance to register.
    """
    _REGISTRY[(engine, mode)] = renderer
    _log.debug("Registered renderer: (%s, %s)", engine, mode.value)


def get_renderer(engine: str, mode: RenderMode) -> DiagramRenderer:
    """Look up the registered renderer for an engine/mode pair.

    Args:
        engine: Diagram engine name.
        mode: Active render mode.

    Returns:
        The registered :class:`DiagramRenderer`.

    Raises:
        DiagramRenderError: If no renderer is registered for the
            requested combination.
    """
    renderer = _REGISTRY.get((engine, mode))
    if renderer is None:
        raise DiagramRenderError(
            block_name=f"{engine}/{mode.value}",
            engine=engine,
            mode=mode.value,
            reason=(
                f"No renderer registered for engine={engine!r}, "
                f"mode={mode.value!r}"
            ),
        )
    return renderer


def render_diagram(
    block: DiagramBlock,
    mode: RenderMode,
) -> str:
    """Render a single diagram block using the appropriate backend.

    Args:
        block: The diagram block to render.
        mode: The active render mode (REQ-024).

    Returns:
        SVG markup produced by the renderer.

    Raises:
        DiagramRenderError: If rendering fails or no renderer is
            available.
    """
    renderer = get_renderer(block.engine, mode)
    try:
        return renderer.render(block.source)
    except DiagramRenderError:
        raise
    except Exception as exc:
        raise DiagramRenderError(
            block_name=f"diagram-{block.index}",
            engine=block.engine,
            mode=mode.value,
            reason=str(exc),
        ) from exc


def render_all_diagrams(
    blocks: tuple[DiagramBlock, ...],
    mode: RenderMode,
) -> dict[int, str]:
    """Render all diagram blocks, collecting results by index.

    Each block is rendered independently.  A failure on one block
    does not prevent rendering of subsequent blocks (REQ-018).
    Failures are logged as warnings and the block is skipped.

    Args:
        blocks: Tuple of diagram blocks to render.
        mode: The active render mode.

    Returns:
        Mapping from diagram index to SVG content for successfully
        rendered blocks.
    """
    results: dict[int, str] = {}
    for block in blocks:
        try:
            svg = render_diagram(block, mode)
        except DiagramRenderError as err:
            _log.warning(
                "Diagram %d (%s) failed: %s",
                block.index,
                block.engine,
                err.reason,
            )
            continue
        results[block.index] = svg
    return results
