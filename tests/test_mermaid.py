"""Tests for the Mermaid rendering pipeline."""

from __future__ import annotations

import hashlib
from email.message import Message
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.error import HTTPError, URLError

import pytest

from scribpy.core import MarkdownCollection, concatenate
from scribpy.core.diagram_blocks import (
    png_filename,
    render_diagram_blocks,
)
from scribpy.core.diagram_encoding import encode_diagram as _encode_diagram
from scribpy.core.manifest import BuildSettings
from scribpy.core.mermaid.cli import MermaidCliRenderer, _execute
from scribpy.core.mermaid.kroki import KrokiRenderer
from scribpy.core.mermaid.local import LocalRenderer
from scribpy.core.mermaid.renderer import make_renderer
from scribpy.errors import MermaidRenderError

_REFERENCE_PREFIX = "assets/generated"


def _write_cli_png(command: list[str]) -> tuple[int, str]:
    """Simulate successful Mermaid CLI PNG creation.

    Args:
        command: Mermaid CLI argument list.

    Returns:
        Successful process return code and standard error.
    """
    output = Path(command[command.index("--output") + 1])
    output.write_bytes(b"cli-png")
    return 0, ""


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
        ) as open_url:
            result = KrokiRenderer().render("graph TD\nA --> B")

        assert result == png
        request = open_url.call_args.args[0]
        assert request.full_url == "https://kroki.io/mermaid/png"
        assert request.method == "POST"
        assert request.data == b"graph TD\nA --> B"
        assert request.get_header("Content-type") == (
            "text/plain; charset=utf-8"
        )

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

    def test_render_reports_http_error_response(self) -> None:
        """Requirement: Kroki HTTP errors expose their response details."""
        error = HTTPError(
            "https://kroki.io/mermaid/png",
            400,
            "Bad Request",
            hdrs=Message(),
            fp=BytesIO(b"Mermaid syntax error on line 2"),
        )

        with (
            patch(
                "scribpy.core.mermaid.kroki.urlopen",
                side_effect=error,
            ),
            pytest.raises(
                MermaidRenderError,
                match="HTTP 400: Mermaid syntax error on line 2",
            ),
        ):
            KrokiRenderer().render("bad diagram")

    def test_render_reports_http_reason_without_response_body(self) -> None:
        """Requirement: empty Kroki errors retain the HTTP reason."""
        error = HTTPError(
            "https://kroki.io/mermaid/png",
            400,
            "Bad Request",
            hdrs=Message(),
            fp=BytesIO(),
        )

        with (
            patch(
                "scribpy.core.mermaid.kroki.urlopen",
                side_effect=error,
            ),
            pytest.raises(MermaidRenderError, match="HTTP 400: Bad Request"),
        ):
            KrokiRenderer().render("bad diagram")


class TestMermaidCliRenderer:
    """Tests for official Mermaid CLI rendering."""

    def test_render_returns_generated_png(self) -> None:
        """Requirement: mmdc output is returned as PNG bytes."""
        with (
            patch(
                "scribpy.core.mermaid.cli.shutil.which",
                return_value="/opt/bin/mmdc",
            ),
            patch(
                "scribpy.core.mermaid.cli._execute",
                side_effect=_write_cli_png,
            ) as run,
        ):
            result = MermaidCliRenderer().render("graph TD\nA --> B")

        command = run.call_args.args[0]
        assert command[0] == "/opt/bin/mmdc"
        assert "--backgroundColor" in command
        assert result == b"cli-png"

    def test_render_rejects_missing_executable(self) -> None:
        """Requirement: a missing mmdc executable raises a domain error."""
        with (
            patch(
                "scribpy.core.mermaid.cli.shutil.which",
                return_value=None,
            ),
            pytest.raises(MermaidRenderError, match="not found"),
        ):
            MermaidCliRenderer("missing-mmdc").render("graph TD\nA --> B")

    def test_render_reports_cli_failure(self) -> None:
        """Requirement: nonzero mmdc exits include standard error."""
        with (
            patch(
                "scribpy.core.mermaid.cli.shutil.which",
                return_value="/opt/bin/mmdc",
            ),
            patch(
                "scribpy.core.mermaid.cli._execute",
                return_value=(2, "invalid diagram"),
            ),
            pytest.raises(MermaidRenderError, match="invalid diagram"),
        ):
            MermaidCliRenderer().render("invalid")

    def test_render_reports_empty_cli_failure(self) -> None:
        """Requirement: empty mmdc errors receive deterministic detail."""
        with (
            patch(
                "scribpy.core.mermaid.cli.shutil.which",
                return_value="/opt/bin/mmdc",
            ),
            patch(
                "scribpy.core.mermaid.cli._execute",
                return_value=(2, ""),
            ),
            pytest.raises(MermaidRenderError, match="no error output"),
        ):
            MermaidCliRenderer().render("invalid")

    def test_render_wraps_timeout(self) -> None:
        """Requirement: mmdc timeouts raise a domain rendering error."""
        with (
            patch(
                "scribpy.core.mermaid.cli.shutil.which",
                return_value="/opt/bin/mmdc",
            ),
            patch(
                "scribpy.core.mermaid.cli._execute",
                side_effect=TimeoutError,
            ),
            pytest.raises(MermaidRenderError, match="execution failed"),
        ):
            MermaidCliRenderer().render("graph TD\nA --> B")

    def test_render_rejects_missing_png(self) -> None:
        """Requirement: successful mmdc runs must produce a PNG."""
        with (
            patch(
                "scribpy.core.mermaid.cli.shutil.which",
                return_value="/opt/bin/mmdc",
            ),
            patch(
                "scribpy.core.mermaid.cli._execute",
                return_value=(0, ""),
            ),
            pytest.raises(MermaidRenderError, match="without producing"),
        ):
            MermaidCliRenderer().render("graph TD\nA --> B")

    def test_execute_runs_process_and_decodes_stderr(self) -> None:
        """Requirement: CLI execution captures decoded standard error."""
        process = MagicMock(returncode=3)
        process.communicate = AsyncMock(return_value=(b"", b"erreur \xff"))

        with patch(
            "scribpy.core.mermaid.cli.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=process),
        ):
            result = _execute(["/opt/bin/mmdc", "--version"])

        assert result == (3, "erreur �")

    def test_execute_stops_process_after_timeout(self) -> None:
        """Requirement: timed-out CLI processes are killed and awaited."""
        process = MagicMock(returncode=1)
        process.communicate = AsyncMock(side_effect=TimeoutError)
        process.wait = AsyncMock()

        with (
            patch(
                "scribpy.core.mermaid.cli.asyncio.create_subprocess_exec",
                new=AsyncMock(return_value=process),
            ),
            pytest.raises(TimeoutError),
        ):
            _execute(["/opt/bin/mmdc"])

        process.kill.assert_called_once_with()
        process.wait.assert_awaited_once_with()


class TestMakeRenderer:
    """Tests for make_renderer factory."""

    def test_make_renderer_web_returns_kroki(self) -> None:
        """Requirement: backend='web' returns a KrokiRenderer instance."""
        assert isinstance(make_renderer("web"), KrokiRenderer)

    def test_make_renderer_kroki_returns_kroki(self) -> None:
        """Requirement: explicit kroki backend returns KrokiRenderer."""
        assert isinstance(make_renderer("kroki"), KrokiRenderer)

    def test_make_renderer_local_returns_local(self) -> None:
        """Requirement: local remains a Mermaid CLI compatibility alias."""
        assert isinstance(make_renderer("local"), LocalRenderer)

    def test_make_renderer_cli_uses_configured_command(self) -> None:
        """Requirement: factory passes the configured mmdc executable."""
        renderer = make_renderer("mermaid_cli", command="custom-mmdc")

        assert isinstance(renderer, MermaidCliRenderer)
        assert renderer.command == "custom-mmdc"

    def test_make_renderer_default_is_kroki(self) -> None:
        """Requirement: Kroki is the default Mermaid backend."""
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


class TestConcatenateWithMermaid:
    """Integration tests for concatenate with Mermaid rendering."""

    def test_concatenate_renders_mermaid_block(self, tmp_path: Path) -> None:
        """Requirement: concatenate replaces mermaid blocks with PNG refs."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "scribpy.yml").write_text(
            "build:\n  mermaid_backend: kroki\n",
            encoding="utf-8",
        )
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

    def test_concatenate_uses_mermaid_cli_backend(
        self, tmp_path: Path
    ) -> None:
        """Requirement: YAML selects the configured Mermaid CLI command."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "scribpy.yml").write_text(
            "build:\n"
            "  mermaid_backend: mermaid_cli\n"
            "  mermaid_command: custom-mmdc\n",
            encoding="utf-8",
        )
        (src / "01-doc.md").write_text(
            "# Doc\n\n```mermaid\ngraph TD\nA --> B\n```\n",
            encoding="utf-8",
        )
        output = tmp_path / "out" / "doc.md"

        with (
            patch(
                "scribpy.core.mermaid.cli.shutil.which",
                return_value="/opt/bin/custom-mmdc",
            ) as which,
            patch(
                "scribpy.core.mermaid.cli._execute",
                side_effect=_write_cli_png,
            ),
        ):
            concatenate(MarkdownCollection.from_tree(src), output)

        which.assert_called_once_with("custom-mmdc")
        assert "![diagram](assets/generated/" in output.read_text(
            encoding="utf-8"
        )

    def test_concatenate_no_mermaid_unchanged(self, tmp_path: Path) -> None:
        """Requirement: document without mermaid blocks is unaffected."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "scribpy.yml").write_text(
            "build:\n  plantuml_backend: kroki\n  mermaid_backend: kroki\n",
            encoding="utf-8",
        )
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
        (src / "scribpy.yml").write_text(
            "build:\n  plantuml_backend: kroki\n  mermaid_backend: kroki\n",
            encoding="utf-8",
        )
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
