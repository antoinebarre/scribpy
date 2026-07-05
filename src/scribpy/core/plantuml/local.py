"""PlantUML renderer backed by a local plantuml.jar installation."""

from __future__ import annotations


class LocalRenderer:
    """Render PlantUML diagrams via a local plantuml.jar installation.

    This backend is not yet implemented. It exists as a placeholder so that
    the factory and the configuration layer can reference it without error.
    """

    def render(self, diagram: str) -> bytes:
        """Render a PlantUML diagram locally.

        Args:
            diagram: PlantUML diagram source, without fenced code delimiters.

        Returns:
            PNG image bytes.

        Raises:
            NotImplementedError: Always. Local rendering is not implemented.
        """
        msg = (
            "The 'local' PlantUML backend is not yet implemented. "
            "Use plantuml_backend: web in your scribpy.yml."
        )
        raise NotImplementedError(msg)
