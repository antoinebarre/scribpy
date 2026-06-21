"""Tests for scribpy.diagrams.plantuml_web."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from scribpy.diagrams.plantuml_web import (
    PlantUmlWebRenderer,
    _plantuml_encode,
)
from scribpy.errors import DiagramRenderError


class TestPlantUmlEncode:
    """Tests for the PlantUML encoding function."""

    def test_encodes_simple_source(self) -> None:
        """Requirement: Encoding produces a non-empty ASCII string."""
        result = _plantuml_encode("@startuml\nA -> B\n@enduml")

        assert result
        assert result.isascii()

    def test_deterministic(self) -> None:
        """Requirement: Same input always produces same encoding."""
        source = "@startuml\nAlice -> Bob\n@enduml"
        assert _plantuml_encode(source) == _plantuml_encode(source)


class TestPlantUmlWebRenderer:
    """Tests for PlantUmlWebRenderer with mocked HTTP."""

    def test_render_success(self) -> None:
        """Requirement: Successful response returns SVG string."""
        renderer = PlantUmlWebRenderer()
        svg_content = "<svg><text>Hello</text></svg>"

        mock_response = MagicMock()
        mock_response.read.return_value = svg_content.encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch(
            "scribpy.diagrams.plantuml_web.urlopen",
            return_value=mock_response,
        ):
            result = renderer.render("@startuml\nA->B\n@enduml")

        assert result == svg_content

    def test_render_network_error(self) -> None:
        """Requirement: Network failure raises DiagramRenderError (REQ-025)."""
        renderer = PlantUmlWebRenderer()

        with (
            patch(
                "scribpy.diagrams.plantuml_web.urlopen",
                side_effect=OSError("Connection refused"),
            ),
            pytest.raises(DiagramRenderError) as exc_info,
        ):
            renderer.render("@startuml\nA->B\n@enduml")

        assert exc_info.value.engine == "plantuml"
        assert exc_info.value.mode == "web"
        assert "Connection refused" in exc_info.value.reason

    def test_render_timeout(self) -> None:
        """Requirement: Timeout raises DiagramRenderError (REQ-025)."""
        renderer = PlantUmlWebRenderer()

        with (
            patch(
                "scribpy.diagrams.plantuml_web.urlopen",
                side_effect=TimeoutError("timed out"),
            ),
            pytest.raises(DiagramRenderError) as exc_info,
        ):
            renderer.render("@startuml\n@enduml")

        assert "timed out" in exc_info.value.reason

    def test_custom_server_url(self) -> None:
        """Requirement: Custom server URL is used in request."""
        renderer = PlantUmlWebRenderer(
            server_url="http://local:8080/plantuml/svg/",
        )

        mock_response = MagicMock()
        mock_response.read.return_value = b"<svg/>"
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch(
            "scribpy.diagrams.plantuml_web.urlopen",
            return_value=mock_response,
        ) as mock_open:
            renderer.render("@startuml\n@enduml")

        call_args = mock_open.call_args
        request = call_args[0][0]
        assert request.full_url.startswith(
            "http://local:8080/plantuml/svg/",
        )
