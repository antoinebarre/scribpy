"""Tests for offline renderer stubs (not yet implemented)."""

import pytest

from scribpy.diagrams.mermaid_offline import MermaidOfflineRenderer
from scribpy.diagrams.plantuml_offline import PlantUmlOfflineRenderer


class TestPlantUmlOfflineRenderer:
    """Tests for the PlantUML offline placeholder."""

    def test_raises_not_implemented(self) -> None:
        """Requirement: Offline mode raises NotImplementedError."""
        renderer = PlantUmlOfflineRenderer()

        with pytest.raises(NotImplementedError, match="not yet implemented"):
            renderer.render("@startuml\nA->B\n@enduml")

    def test_accepts_jar_path(self) -> None:
        """Requirement: Constructor accepts jar_path for future use."""
        renderer = PlantUmlOfflineRenderer(jar_path="/opt/plantuml.jar")
        assert renderer.jar_path == "/opt/plantuml.jar"


class TestMermaidOfflineRenderer:
    """Tests for the Mermaid offline placeholder."""

    def test_raises_not_implemented(self) -> None:
        """Requirement: Offline mode raises NotImplementedError."""
        renderer = MermaidOfflineRenderer()

        with pytest.raises(NotImplementedError, match="not yet implemented"):
            renderer.render("graph TD\n  A-->B")
