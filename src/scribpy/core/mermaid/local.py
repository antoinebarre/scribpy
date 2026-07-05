"""Mermaid renderer backed by a local mermaid-cli installation."""

from __future__ import annotations


class LocalRenderer:
    """Render Mermaid diagrams via a local mermaid-cli installation.

    This backend is not yet implemented.  It exists as a placeholder so that
    the factory and the configuration layer can reference it without error.
    """

    def render(self, diagram: str) -> bytes:
        """Render a Mermaid diagram locally.

        Args:
            diagram: Mermaid diagram source, without fenced code delimiters.

        Returns:
            PNG image bytes.

        Raises:
            NotImplementedError: Always. Local rendering is not implemented.
        """
        msg = (
            "The 'local' Mermaid backend is not yet implemented. "
            "Use mermaid_backend: web in your scribpy.yml."
        )
        raise NotImplementedError(msg)
