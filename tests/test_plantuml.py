"""Tests for the PlantUML rendering pipeline."""

from __future__ import annotations

import hashlib
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import URLError

import pytest

from scribpy.core import MarkdownCollection, concatenate
from scribpy.core.assembly.plantuml_transform import (
    _png_filename,
    render_plantuml_blocks,
)
from scribpy.core.plantuml.local import LocalRenderer
from scribpy.core.plantuml.renderer import make_renderer
from scribpy.core.plantuml.web_server import (
    WebServerRenderer,
    _encode_diagram,
    _plantuml_b64encode,
)
from scribpy.errors import PlantUmlRenderError


class TestPngFilename:
    """Tests for the _png_filename helper."""

    def test_png_filename_returns_sha256_hex(self) -> None:
        """Requirement: filename is the SHA-256 hex digest of the diagram."""
        diagram = "@startuml\nA -> B\n@enduml\n"
        expected = hashlib.sha256(diagram.encode("utf-8")).hexdigest() + ".png"
        assert _png_filename(diagram) == expected

    def test_png_filename_differs_for_different_diagrams(self) -> None:
        """Requirement: different diagrams produce different filenames."""
        assert _png_filename("A") != _png_filename("B")

    def test_png_filename_is_stable(self) -> None:
        """Requirement: same diagram always produces the same filename."""
        assert _png_filename("X") == _png_filename("X")


class TestEncodeDiagram:
    """Tests for the _encode_diagram helper in web_server.py."""

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

    def test_encode_diagram_two_byte_remainder(self) -> None:
        """Requirement: two trailing bytes are encoded to 3 characters."""
        data = b"\x01\x02"
        result = _plantuml_b64encode(data)
        assert isinstance(result, str)
        assert len(result) == 3
        assert result.isascii()


class TestWebServerRenderer:
    """Tests for WebServerRenderer."""

    def test_render_returns_png_bytes_on_success(self) -> None:
        """Requirement: successful HTTP 200 response returns PNG bytes."""
        png = b"\x89PNG\r\n\x1a\n"
        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.status = 200
        mock_response.read.return_value = png

        with patch(
            "scribpy.core.plantuml.web_server.urlopen",
            return_value=mock_response,
        ):
            result = WebServerRenderer().render("@startuml\nA -> B\n@enduml")

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
                "scribpy.core.plantuml.web_server.urlopen",
                return_value=mock_response,
            ),
            pytest.raises(PlantUmlRenderError, match="HTTP 400"),
        ):
            WebServerRenderer().render("bad diagram")

    def test_render_raises_on_url_error(self) -> None:
        """Requirement: URLError is wrapped in PlantUmlRenderError."""
        with (
            patch(
                "scribpy.core.plantuml.web_server.urlopen",
                side_effect=URLError("connection refused"),
            ),
            pytest.raises(PlantUmlRenderError, match="connection refused"),
        ):
            WebServerRenderer().render("@startuml\nA -> B\n@enduml")


class TestLocalRenderer:
    """Tests for LocalRenderer."""

    def test_render_raises_not_implemented(self) -> None:
        """Requirement: local backend raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="local"):
            LocalRenderer().render("@startuml\nA -> B\n@enduml")


class TestMakeRenderer:
    """Tests for make_renderer factory."""

    def test_make_renderer_web_returns_web_server(self) -> None:
        """Requirement: backend='web' returns a WebServerRenderer instance."""
        assert isinstance(make_renderer("web"), WebServerRenderer)

    def test_make_renderer_local_returns_local(self) -> None:
        """Requirement: backend='local' returns a LocalRenderer instance."""
        assert isinstance(make_renderer("local"), LocalRenderer)

    def test_make_renderer_default_is_web(self) -> None:
        """Requirement: default backend is 'web'."""
        assert isinstance(make_renderer(), WebServerRenderer)

    def test_make_renderer_raises_for_unknown_backend(self) -> None:
        """Requirement: unknown backend name raises ValueError."""
        with pytest.raises(ValueError, match="unknown_backend"):
            make_renderer("unknown_backend")


class TestRenderPlantumlBlocks:
    """Tests for render_plantuml_blocks."""

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

        result = render_plantuml_blocks(content, renderer, generated)

        assert "![diagram](assets/generated/" in result
        assert ".png)" in result

    def test_writes_png_to_generated_dir(self, tmp_path: Path) -> None:
        """Requirement: PNG bytes are written to the generated directory."""
        png = b"\x89PNG\r\n"
        content = "```plantuml\n@startuml\nA -> B\n@enduml\n```\n"
        renderer = self._fake_renderer(png)
        generated = tmp_path / "assets" / "generated"

        render_plantuml_blocks(content, renderer, generated)

        files = list(generated.iterdir())
        assert len(files) == 1
        assert files[0].read_bytes() == png

    def test_does_not_recopy_identical_diagram(self, tmp_path: Path) -> None:
        """Requirement: identical diagrams are rendered only once on disk."""
        content = (
            "```plantuml\n@startuml\nA -> B\n@enduml\n```\n"
            "```plantuml\n@startuml\nA -> B\n@enduml\n```\n"
        )
        renderer = self._fake_renderer()
        generated = tmp_path / "assets" / "generated"

        render_plantuml_blocks(content, renderer, generated)

        assert len(list(generated.iterdir())) == 1
        assert renderer.render.call_count == 2

    def test_creates_generated_dir_if_missing(self, tmp_path: Path) -> None:
        """Requirement: generated dir is created when absent."""
        content = "```plantuml\n@startuml\nA -> B\n@enduml\n```\n"
        renderer = self._fake_renderer()
        generated = tmp_path / "deep" / "nested" / "generated"

        render_plantuml_blocks(content, renderer, generated)

        assert generated.is_dir()

    def test_leaves_content_without_plantuml_unchanged(
        self, tmp_path: Path
    ) -> None:
        """Requirement: content with no plantuml blocks is returned as-is."""
        content = "# Title\n\nSome text.\n"
        renderer = self._fake_renderer()
        generated = tmp_path / "generated"

        result = render_plantuml_blocks(content, renderer, generated)

        assert result == content
        renderer.render.assert_not_called()

    def test_handles_multiple_different_diagrams(self, tmp_path: Path) -> None:
        """Requirement: each unique diagram gets its own PNG file."""
        content = (
            "```plantuml\n@startuml\nA -> B\n@enduml\n```\n"
            "```plantuml\n@startuml\nC -> D\n@enduml\n```\n"
        )
        renderer = self._fake_renderer()
        generated = tmp_path / "generated"

        result = render_plantuml_blocks(content, renderer, generated)

        assert len(list(generated.iterdir())) == 2
        assert result.count("![diagram]") == 2

    def test_plantuml_block_case_insensitive(self, tmp_path: Path) -> None:
        """Requirement: plantuml fence tag is matched case-insensitively."""
        content = "```PlantUML\n@startuml\nA -> B\n@enduml\n```\n"
        renderer = self._fake_renderer()
        generated = tmp_path / "generated"

        result = render_plantuml_blocks(content, renderer, generated)

        assert "![diagram]" in result


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
            "scribpy.core.plantuml.web_server.urlopen",
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
