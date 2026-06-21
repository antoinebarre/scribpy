"""Mermaid offline renderer — not yet implemented.

This module will eventually render Mermaid diagrams locally.
Currently raises :class:`NotImplementedError`.
"""

from __future__ import annotations


class MermaidOfflineRenderer:
    """Placeholder for offline Mermaid rendering.

    This will use a local rendering tool (e.g. ``mmdc``) once
    implemented.
    """

    def render(self, source: str) -> str:
        """Render Mermaid source locally.

        Args:
            source: Raw Mermaid diagram source.

        Returns:
            SVG markup as a string.

        Raises:
            NotImplementedError: Always — offline mode is not yet
                available.
        """
        msg = (
            "Mermaid offline rendering is not yet implemented. "
            "Use render_mode='web' instead."
        )
        raise NotImplementedError(msg)
