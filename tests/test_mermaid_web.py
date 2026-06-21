"""Tests for scribpy.diagrams.mermaid_web."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from scribpy.diagrams.mermaid_web import MermaidWebRenderer
from scribpy.errors import DiagramRenderError


class TestMermaidWebRenderer:
    """Tests for MermaidWebRenderer with mocked HTTP."""

    def test_render_success(self) -> None:
        """Requirement: Successful response returns SVG string."""
        renderer = MermaidWebRenderer()
        svg_content = "<svg><rect/></svg>"

        mock_response = MagicMock()
        mock_response.read.return_value = svg_content.encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch(
            "scribpy.diagrams.mermaid_web.urlopen",
            return_value=mock_response,
        ):
            result = renderer.render("graph TD\n  A-->B")

        assert result == svg_content

    def test_render_network_error(self) -> None:
        """Requirement: Network failure raises DiagramRenderError (REQ-025)."""
        renderer = MermaidWebRenderer()

        with (
            patch(
                "scribpy.diagrams.mermaid_web.urlopen",
                side_effect=OSError("Network unreachable"),
            ),
            pytest.raises(DiagramRenderError) as exc_info,
        ):
            renderer.render("graph TD\n  A-->B")

        assert exc_info.value.engine == "mermaid"
        assert exc_info.value.mode == "web"
        assert "Network unreachable" in exc_info.value.reason

    def test_render_timeout(self) -> None:
        """Requirement: Timeout raises DiagramRenderError (REQ-025)."""
        renderer = MermaidWebRenderer()

        with (
            patch(
                "scribpy.diagrams.mermaid_web.urlopen",
                side_effect=TimeoutError("timed out"),
            ),
            pytest.raises(DiagramRenderError) as exc_info,
        ):
            renderer.render("graph TD")

        assert "timed out" in exc_info.value.reason

    def test_url_contains_base64_encoded_source(self) -> None:
        """Requirement: Source is base64-encoded in the request URL."""
        renderer = MermaidWebRenderer()

        mock_response = MagicMock()
        mock_response.read.return_value = b"<svg/>"
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch(
            "scribpy.diagrams.mermaid_web.urlopen",
            return_value=mock_response,
        ) as mock_open:
            renderer.render("graph TD\n  A-->B")

        call_args = mock_open.call_args
        request = call_args[0][0]
        assert request.full_url.startswith("https://mermaid.ink/svg/")

    def test_custom_server_url(self) -> None:
        """Requirement: Custom server URL is used in request."""
        renderer = MermaidWebRenderer(
            server_url="http://local:9000/svg/",
        )

        mock_response = MagicMock()
        mock_response.read.return_value = b"<svg/>"
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch(
            "scribpy.diagrams.mermaid_web.urlopen",
            return_value=mock_response,
        ) as mock_open:
            renderer.render("graph LR")

        call_args = mock_open.call_args
        request = call_args[0][0]
        assert request.full_url.startswith("http://local:9000/svg/")
