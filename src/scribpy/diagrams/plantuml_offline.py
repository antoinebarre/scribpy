"""PlantUML offline renderer — not yet implemented.

This module will eventually render PlantUML diagrams locally via
the PlantUML JAR file.  Currently raises :class:`NotImplementedError`.
"""

from __future__ import annotations


class PlantUmlOfflineRenderer:
    """Placeholder for offline PlantUML rendering via local JAR.

    Attributes:
        jar_path: Path to the PlantUML JAR (unused until implemented).
    """

    def __init__(self, jar_path: str | None = None) -> None:
        """Initialise with an optional JAR path.

        Args:
            jar_path: Path to the PlantUML JAR file.
        """
        self.jar_path = jar_path

    def render(self, source: str) -> str:
        """Render PlantUML source locally.

        Args:
            source: Raw PlantUML diagram source.

        Returns:
            SVG markup as a string.

        Raises:
            NotImplementedError: Always — offline mode is not yet
                available.
        """
        msg = (
            "PlantUML offline rendering is not yet implemented. "
            "Use render_mode='web' instead."
        )
        raise NotImplementedError(msg)
