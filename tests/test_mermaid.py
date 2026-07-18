"""Tests for the Mermaid rendering pipeline."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import URLError

import pytest

from scribpy.core import MarkdownCollection, concatenate
from scribpy.core.diagram_blocks import (
    png_filename,
    render_blocks,
    render_diagram_blocks,
)
from scribpy.core.diagram_encoding import encode_diagram as _encode_diagram
from scribpy.core.manifest import BuildSettings
from scribpy.core.mermaid.kroki import KrokiRenderer
from scribpy.core.mermaid.local import LocalRenderer
from scribpy.core.mermaid.renderer import make_renderer
from scribpy.errors import MermaidRenderError

_MERMAID_BLOCK = re.compile(
    r"^```mermaid\n(?P<diagram>.*?)^```",
    re.DOTALL | re.MULTILINE | re.IGNORECASE,
)
_REFERENCE_PREFIX = "assets/generated"


class TestPngFilename:
    """Tests for the _png_filename helper."""

    def test_png_filename_returns_sha256_hex(self) -> None:
        """Requirement: filename is the SHA-256 hex digest of the diagram."""
        diagram = "graph TD\nA --> B\n"
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

    def test_encode_diagram_returns_ascii_string(self) -> None:
        """Requirement: encoded result is an ASCII string."""
        result = _encode_diagram("graph TD\nA --> B")
        assert isinstance(result, str)
        assert result.isascii()

    def test_encode_diagram_is_deterministic(self) -> None:
        """Requirement: same source always produces the same encoding."""
        src = "graph TD\nA --> B"
        assert _encode_diagram(src) == _encode_diagram(src)

    def test_encode_diagram_differs_for_different_sources(self) -> None:
        """Requirement: different sources produce different encodings."""
        assert _encode_diagram("graph TD\nA --> B") != _encode_diagram(
            "graph LR\nA --> B"
        )


class TestKrokiRenderer:
    """Tests for KrokiRenderer."""

    def test_render_returns_png_bytes_on_success(self) -> None:
        """Requirement: successful HTTP 200 response returns PNG bytes."""
        png = b"\x89PNG\r\n\x1a\n"
        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.status = 200
        mock_response.read.return_value = png

        with patch(
            "scribpy.core.mermaid.kroki.urlopen", return_value=mock_response
        ):
            result = KrokiRenderer().render("graph TD\nA --> B")

        assert result == png

    def test_render_raises_on_non_200_status(self) -> None:
        """Requirement: non-200 HTTP response raises MermaidRenderError."""
        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.status = 400
        mock_response.read.return_value = b""

        with (
            patch(
                "scribpy.core.mermaid.kroki.urlopen",
                return_value=mock_response,
            ),
            pytest.raises(MermaidRenderError, match="HTTP 400"),
        ):
            KrokiRenderer().render("bad diagram")

    def test_render_raises_on_url_error(self) -> None:
        """Requirement: URLError is wrapped in MermaidRenderError."""
        with (
            patch(
                "scribpy.core.mermaid.kroki.urlopen",
                side_effect=URLError("connection refused"),
            ),
            pytest.raises(MermaidRenderError, match="connection refused"),
        ):
            KrokiRenderer().render("graph TD\nA --> B")


class TestLocalRenderer:
    """Tests for LocalRenderer."""

    def test_render_raises_not_implemented(self) -> None:
        """Requirement: local backend raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="local"):
            LocalRenderer().render("graph TD\nA --> B")


class TestMakeRenderer:
    """Tests for make_renderer factory."""

    def test_make_renderer_web_returns_kroki(self) -> None:
        """Requirement: backend='web' returns a KrokiRenderer instance."""
        assert isinstance(make_renderer("web"), KrokiRenderer)

    def test_make_renderer_local_returns_local(self) -> None:
        """Requirement: backend='local' returns a LocalRenderer instance."""
        assert isinstance(make_renderer("local"), LocalRenderer)

    def test_make_renderer_default_is_web(self) -> None:
        """Requirement: default backend is 'web'."""
        assert isinstance(make_renderer(), KrokiRenderer)

    def test_make_renderer_raises_for_unknown_backend(self) -> None:
        """Requirement: unknown backend name raises ValueError."""
        with pytest.raises(ValueError, match="unknown_backend"):
            make_renderer("unknown_backend")


class TestRenderMermaidBlocks:
    """Tests for generic Mermaid block rendering."""

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

    def test_replaces_mermaid_block_with_image(self, tmp_path: Path) -> None:
        """Requirement: mermaid block is replaced by an image reference."""
        content = "```mermaid\ngraph TD\nA --> B\n```\n"
        renderer = self._fake_renderer()
        generated = tmp_path / "assets" / "generated"

        with (
            patch("scribpy.core.diagram_blocks.make_plantuml_renderer"),
            patch(
                "scribpy.core.diagram_blocks.make_mermaid_renderer",
                return_value=renderer,
            ),
        ):
            result = render_diagram_blocks(
                content,
                BuildSettings(),
                generated,
                _REFERENCE_PREFIX,
            )

        assert "![diagram](assets/generated/" in result
        assert ".png)" in result

    def test_writes_png_to_generated_dir(self, tmp_path: Path) -> None:
        """Requirement: PNG bytes are written to the generated directory."""
        png = b"\x89PNG\r\n"
        content = "```mermaid\ngraph TD\nA --> B\n```\n"
        renderer = self._fake_renderer(png)
        generated = tmp_path / "assets" / "generated"

        render_blocks(
            content,
            renderer,
            generated,
            _REFERENCE_PREFIX,
            _MERMAID_BLOCK,
        )

        files = list(generated.iterdir())
        assert len(files) == 1
        assert files[0].read_bytes() == png

    def test_does_not_recopy_identical_diagram(self, tmp_path: Path) -> None:
        """Requirement: identical diagrams are rendered only once on disk."""
        content = (
            "```mermaid\ngraph TD\nA --> B\n```\n"
            "```mermaid\ngraph TD\nA --> B\n```\n"
        )
        renderer = self._fake_renderer()
        generated = tmp_path / "assets" / "generated"

        render_blocks(
            content,
            renderer,
            generated,
            _REFERENCE_PREFIX,
            _MERMAID_BLOCK,
        )

        assert len(list(generated.iterdir())) == 1
        assert renderer.render.call_count == 1

    def test_creates_generated_dir_if_missing(self, tmp_path: Path) -> None:
        """Requirement: generated dir is created when absent."""
        content = "```mermaid\ngraph TD\nA --> B\n```\n"
        renderer = self._fake_renderer()
        generated = tmp_path / "deep" / "nested" / "generated"

        render_blocks(
            content,
            renderer,
            generated,
            _REFERENCE_PREFIX,
            _MERMAID_BLOCK,
        )

        assert generated.is_dir()

    def test_leaves_content_without_mermaid_unchanged(
        self, tmp_path: Path
    ) -> None:
        """Requirement: content with no mermaid blocks is returned as-is."""
        content = "# Title\n\nSome text.\n"
        renderer = self._fake_renderer()
        generated = tmp_path / "generated"

        result = render_blocks(
            content,
            renderer,
            generated,
            _REFERENCE_PREFIX,
            _MERMAID_BLOCK,
        )

        assert result == content
        renderer.render.assert_not_called()

    def test_handles_multiple_different_diagrams(self, tmp_path: Path) -> None:
        """Requirement: each unique diagram gets its own PNG file."""
        content = (
            "```mermaid\ngraph TD\nA --> B\n```\n"
            "```mermaid\ngraph LR\nC --> D\n```\n"
        )
        renderer = self._fake_renderer()
        generated = tmp_path / "generated"

        result = render_blocks(
            content,
            renderer,
            generated,
            _REFERENCE_PREFIX,
            _MERMAID_BLOCK,
        )

        assert len(list(generated.iterdir())) == 2
        assert result.count("![diagram]") == 2

    def test_mermaid_block_case_insensitive(self, tmp_path: Path) -> None:
        """Requirement: mermaid fence tag is matched case-insensitively."""
        content = "```Mermaid\ngraph TD\nA --> B\n```\n"
        renderer = self._fake_renderer()
        generated = tmp_path / "generated"

        result = render_blocks(
            content,
            renderer,
            generated,
            _REFERENCE_PREFIX,
            _MERMAID_BLOCK,
        )

        assert "![diagram]" in result


class TestConcatenateWithMermaid:
    """Integration tests for concatenate with Mermaid rendering."""

    def test_concatenate_renders_mermaid_block(self, tmp_path: Path) -> None:
        """Requirement: concatenate replaces mermaid blocks with PNG refs."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "01-doc.md").write_text(
            "# Doc\n\n```mermaid\ngraph TD\nA --> B\n```\n",
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
            "scribpy.core.mermaid.kroki.urlopen", return_value=mock_response
        ):
            concatenate(collection, output)

        text = output.read_text(encoding="utf-8")
        assert "![diagram](assets/generated/" in text
        assert "```mermaid" not in text
        assert (tmp_path / "out" / "assets" / "generated").is_dir()

    def test_concatenate_uses_local_mermaid_backend(
        self, tmp_path: Path
    ) -> None:
        """Requirement: mermaid_backend: local raises NotImplementedError."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "scribpy.yml").write_text(
            "build:\n  mermaid_backend: local\n", encoding="utf-8"
        )
        (src / "01-doc.md").write_text(
            "# Doc\n\n```mermaid\ngraph TD\nA --> B\n```\n",
            encoding="utf-8",
        )
        output = tmp_path / "out" / "doc.md"

        collection = MarkdownCollection.from_tree(src)
        with pytest.raises(NotImplementedError, match="local"):
            concatenate(collection, output)

    def test_concatenate_no_mermaid_unchanged(self, tmp_path: Path) -> None:
        """Requirement: document without mermaid blocks is unaffected."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "01-doc.md").write_text(
            "# Doc\n\nJust text.\n", encoding="utf-8"
        )
        output = tmp_path / "out" / "doc.md"

        collection = MarkdownCollection.from_tree(src)
        concatenate(collection, output)

        text = output.read_text(encoding="utf-8")
        assert "```mermaid" not in text
        assert "![diagram]" not in text

    def test_concatenate_renders_both_plantuml_and_mermaid(
        self, tmp_path: Path
    ) -> None:
        """Requirement: both plantuml and mermaid blocks are rendered."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "01-doc.md").write_text(
            "# Doc\n\n"
            "```plantuml\n@startuml\nA -> B\n@enduml\n```\n\n"
            "```mermaid\ngraph TD\nA --> B\n```\n",
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
        with (
            patch(
                "scribpy.core.plantuml.kroki.urlopen",
                return_value=mock_response,
            ),
            patch(
                "scribpy.core.mermaid.kroki.urlopen",
                return_value=mock_response,
            ),
        ):
            concatenate(collection, output)

        text = output.read_text(encoding="utf-8")
        assert text.count("![diagram](assets/generated/") == 2
        assert "```plantuml" not in text
        assert "```mermaid" not in text
