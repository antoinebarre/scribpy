"""Tests for the PlantUML rendering pipeline."""

from __future__ import annotations

import hashlib
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import URLError

import pytest

from scribpy.core import MarkdownCollection, concatenate
from scribpy.core.diagram_blocks import (
    png_filename,
    render_diagram_blocks,
)
from scribpy.core.diagram_encoding import encode_diagram as _encode_diagram
from scribpy.core.manifest import BuildSettings
from scribpy.core.plantuml.kroki import KrokiRenderer
from scribpy.core.plantuml.local import LocalRenderer
from scribpy.core.plantuml.renderer import make_renderer
from scribpy.core.plantuml.server import PlantUmlServerRenderer
from scribpy.errors import PlantUmlRenderError

_REFERENCE_PREFIX = "assets/generated"


class TestPngFilename:
    """Tests for the _png_filename helper."""

    def test_png_filename_returns_sha256_hex(self) -> None:
        """Requirement: filename is the SHA-256 hex digest of the diagram."""
        diagram = "@startuml\nA -> B\n@enduml\n"
        expected = hashlib.sha256(diagram.encode("utf-8")).hexdigest() + ".png"
        assert png_filename(diagram) == expected

    def test_png_filename_differs_for_different_diagrams(self) -> None:
        """Requirement: different diagrams produce different filenames."""
        assert png_filename("A") != png_filename("B")

    def test_png_filename_is_stable(self) -> None:
        """Requirement: same diagram always produces the same filename."""
        assert png_filename("X") == png_filename("X")


class TestEncodeDiagram:
    """Tests for the encode_diagram helper in diagram_encoding.py."""

    def test_encode_diagram_returns_string(self) -> None:
        """Requirement: encoded result is an ASCII string."""
        result = _encode_diagram("@startuml\nA -> B\n@enduml")
        assert isinstance(result, str)
        assert result.isascii()

    def test_encode_diagram_is_deterministic(self) -> None:
        """Requirement: same source always produces the same encoding."""
        src = "@startuml\nA -> B\n@enduml"
        assert _encode_diagram(src) == _encode_diagram(src)

    def test_encode_diagram_differs_for_different_sources(self) -> None:
        """Requirement: different sources produce different encodings."""
        assert _encode_diagram("A") != _encode_diagram("B")


class TestKrokiRenderer:
    """Tests for plantuml KrokiRenderer."""

    def test_render_returns_png_bytes_on_success(self) -> None:
        """Requirement: successful HTTP 200 response returns PNG bytes."""
        png = b"\x89PNG\r\n\x1a\n"
        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.status = 200
        mock_response.read.return_value = png

        with patch(
            "scribpy.core.plantuml.kroki.urlopen",
            return_value=mock_response,
        ):
            result = KrokiRenderer().render("@startuml\nA -> B\n@enduml")

        assert result == png

    def test_render_raises_on_non_200_status(self) -> None:
        """Requirement: non-200 HTTP response raises PlantUmlRenderError."""
        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.status = 400
        mock_response.read.return_value = b""

        with (
            patch(
                "scribpy.core.plantuml.kroki.urlopen",
                return_value=mock_response,
            ),
            pytest.raises(PlantUmlRenderError, match="HTTP 400"),
        ):
            KrokiRenderer().render("bad diagram")

    def test_render_raises_on_url_error(self) -> None:
        """Requirement: URLError is wrapped in PlantUmlRenderError."""
        with (
            patch(
                "scribpy.core.plantuml.kroki.urlopen",
                side_effect=URLError("connection refused"),
            ),
            pytest.raises(PlantUmlRenderError, match="connection refused"),
        ):
            KrokiRenderer().render("@startuml\nA -> B\n@enduml")


class TestLocalRenderer:
    """Tests for LocalRenderer."""

    def test_render_raises_not_implemented(self) -> None:
        """Requirement: local backend raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="local"):
            LocalRenderer().render("@startuml\nA -> B\n@enduml")


class TestMakeRenderer:
    """Tests for make_renderer factory."""

    def test_make_renderer_web_returns_kroki(self) -> None:
        """Requirement: backend='web' returns a KrokiRenderer instance."""
        assert isinstance(make_renderer("web"), KrokiRenderer)

    def test_make_renderer_kroki_returns_kroki(self) -> None:
        """Requirement: explicit kroki backend returns KrokiRenderer."""
        assert isinstance(make_renderer("kroki"), KrokiRenderer)

    def test_make_renderer_plantuml_server_uses_configured_url(self) -> None:
        """Requirement: server backend receives its configured base URL."""
        renderer = make_renderer(
            "plantuml_server",
            server_url="https://plantuml.example.test/service",
        )

        assert isinstance(renderer, PlantUmlServerRenderer)
        assert renderer.server_url == "https://plantuml.example.test/service"

    def test_make_renderer_local_returns_local(self) -> None:
        """Requirement: backend='local' returns a LocalRenderer instance."""
        assert isinstance(make_renderer("local"), LocalRenderer)

    def test_make_renderer_default_is_plantuml_server(self) -> None:
        """Requirement: PlantUML Server is the default backend."""
        assert isinstance(make_renderer(), PlantUmlServerRenderer)

    def test_make_renderer_raises_for_unknown_backend(self) -> None:
        """Requirement: unknown backend name raises ValueError."""
        with pytest.raises(ValueError, match="unknown_backend"):
            make_renderer("unknown_backend")


class TestPlantUmlServerRenderer:
    """Tests for PlantUML Server HTTP rendering."""

    def test_render_requests_hex_encoded_png(self) -> None:
        """Requirement: server rendering uses official hexadecimal URLs."""
        png = b"\x89PNG\r\n\x1a\n"
        response = MagicMock()
        response.__enter__ = MagicMock(return_value=response)
        response.__exit__ = MagicMock(return_value=False)
        response.status = 200
        response.read.return_value = png
        diagram = "@startuml\nAlice -> Bob : hé\n@enduml"

        with patch(
            "scribpy.core.plantuml.server.urlopen",
            return_value=response,
        ) as request:
            result = PlantUmlServerRenderer(
                "https://plantuml.example.test/plantuml/"
            ).render(diagram)

        encoded = f"~h{diagram.encode('utf-8').hex()}"
        sent_request = request.call_args.args[0]
        assert sent_request.full_url == (
            f"https://plantuml.example.test/plantuml/png/{encoded}"
        )
        assert result == png

    def test_render_raises_on_non_200_status(self) -> None:
        """Requirement: server HTTP failures raise PlantUmlRenderError."""
        response = MagicMock()
        response.__enter__ = MagicMock(return_value=response)
        response.__exit__ = MagicMock(return_value=False)
        response.status = 503

        with (
            patch(
                "scribpy.core.plantuml.server.urlopen",
                return_value=response,
            ),
            pytest.raises(PlantUmlRenderError, match="HTTP 503"),
        ):
            PlantUmlServerRenderer().render("@startuml\nA -> B\n@enduml")

    def test_render_wraps_network_error(self) -> None:
        """Requirement: server network failures use the domain error."""
        with (
            patch(
                "scribpy.core.plantuml.server.urlopen",
                side_effect=URLError("server unavailable"),
            ),
            pytest.raises(
                PlantUmlRenderError,
                match="server unavailable",
            ),
        ):
            PlantUmlServerRenderer().render("@startuml\nA -> B\n@enduml")


class TestRenderPlantumlBlocks:
    """Tests for generic PlantUML block rendering."""

    def _fake_renderer(self, png: bytes = b"\x89PNG") -> MagicMock:
        """Return a mock renderer that returns fixed PNG bytes.

        Args:
            png: PNG bytes the mock renderer will return.

        Returns:
            Mock renderer instance.
        """
        renderer = MagicMock()
        renderer.render.return_value = png
        return renderer

    def test_replaces_plantuml_block_with_image(self, tmp_path: Path) -> None:
        """Requirement: plantuml block is replaced by an image reference."""
        content = "```plantuml\n@startuml\nA -> B\n@enduml\n```\n"
        renderer = self._fake_renderer()
        generated = tmp_path / "assets" / "generated"

        with (
            patch(
                "scribpy.core.diagram_blocks.make_plantuml_renderer",
                return_value=renderer,
            ),
            patch("scribpy.core.diagram_blocks.make_mermaid_renderer"),
        ):
            result = render_diagram_blocks(
                content,
                BuildSettings(),
                generated,
                _REFERENCE_PREFIX,
            )

        assert "![diagram](assets/generated/" in result
        assert ".png)" in result


class TestConcatenateWithPlantuml:
    """Integration tests for concatenate with PlantUML rendering."""

    def test_concatenate_renders_plantuml_block(self, tmp_path: Path) -> None:
        """Requirement: concatenate replaces plantuml blocks with PNG refs."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "01-doc.md").write_text(
            "# Doc\n\n```plantuml\n@startuml\nA -> B\n@enduml\n```\n",
            encoding="utf-8",
        )
        output = tmp_path / "out" / "doc.md"
        png = b"\x89PNG\r\n\x1a\n"

        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.status = 200
        mock_response.read.return_value = png

        collection = MarkdownCollection.from_tree(src)
        with patch(
            "scribpy.core.plantuml.kroki.urlopen",
            return_value=mock_response,
        ):
            concatenate(collection, output)

        text = output.read_text(encoding="utf-8")
        assert "![diagram](assets/generated/" in text
        assert "```plantuml" not in text
        assert (tmp_path / "out" / "assets" / "generated").is_dir()

    def test_concatenate_uses_local_backend_from_manifest(
        self, tmp_path: Path
    ) -> None:
        """Requirement: plantuml_backend: local raises NotImplementedError."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "scribpy.yml").write_text(
            "build:\n  plantuml_backend: local\n", encoding="utf-8"
        )
        (src / "01-doc.md").write_text(
            "# Doc\n\n```plantuml\n@startuml\nA -> B\n@enduml\n```\n",
            encoding="utf-8",
        )
        output = tmp_path / "out" / "doc.md"

        collection = MarkdownCollection.from_tree(src)
        with pytest.raises(NotImplementedError, match="local"):
            concatenate(collection, output)

    def test_concatenate_uses_plantuml_server_from_manifest(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: YAML selects the configured PlantUML Server."""
        source = tmp_path / "src"
        source.mkdir()
        (source / "scribpy.yml").write_text(
            "build:\n"
            "  plantuml_backend: plantuml_server\n"
            "  plantuml_server_url: https://uml.example.test/plantuml\n",
            encoding="utf-8",
        )
        (source / "diagram.md").write_text(
            "# Diagram\n\n```plantuml\n@startuml\nA -> B\n@enduml\n```\n",
            encoding="utf-8",
        )
        response = MagicMock()
        response.__enter__ = MagicMock(return_value=response)
        response.__exit__ = MagicMock(return_value=False)
        response.status = 200
        response.read.return_value = b"png"

        with patch(
            "scribpy.core.plantuml.server.urlopen",
            return_value=response,
        ) as request:
            concatenate(
                MarkdownCollection.from_tree(source),
                tmp_path / "output" / "document.md",
            )

        sent_request = request.call_args.args[0]
        assert sent_request.full_url.startswith(
            "https://uml.example.test/plantuml/png/~h"
        )

    def test_concatenate_no_plantuml_unchanged(self, tmp_path: Path) -> None:
        """Requirement: document without plantuml blocks is unaffected."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "01-doc.md").write_text(
            "# Doc\n\nJust text.\n", encoding="utf-8"
        )
        output = tmp_path / "out" / "doc.md"

        collection = MarkdownCollection.from_tree(src)
        concatenate(collection, output)

        text = output.read_text(encoding="utf-8")
        assert "```plantuml" not in text
        assert "![diagram]" not in text
