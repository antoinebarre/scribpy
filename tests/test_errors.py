"""Tests for scribpy.errors — exception hierarchy."""

import pytest

from scribpy.errors import (
    DiagramRenderError,
    ImageNotFoundError,
    InvalidMarkdownError,
    ScribpyError,
)


class TestScribpyError:
    """Tests for the base ScribpyError."""

    def test_is_exception(self) -> None:
        """Requirement: ScribpyError is a standard Exception."""
        assert issubclass(ScribpyError, Exception)

    def test_can_be_raised_and_caught(self) -> None:
        """Requirement: ScribpyError can be raised and caught."""
        with pytest.raises(ScribpyError):
            raise ScribpyError("boom")


class TestImageNotFoundError:
    """Tests for ImageNotFoundError."""

    def test_inherits_from_scribpy_error(self) -> None:
        """Requirement: catchable via ScribpyError."""
        assert issubclass(ImageNotFoundError, ScribpyError)

    def test_stores_path(self) -> None:
        """Requirement: the missing path is accessible."""
        err = ImageNotFoundError("img/logo.png")
        assert err.path == "img/logo.png"

    def test_message_contains_path(self) -> None:
        """Requirement: the error message names the path."""
        err = ImageNotFoundError("img/logo.png")
        assert "img/logo.png" in str(err)


class TestDiagramRenderError:
    """Tests for DiagramRenderError."""

    def test_inherits_from_scribpy_error(self) -> None:
        """Requirement: catchable via ScribpyError."""
        assert issubclass(DiagramRenderError, ScribpyError)

    def test_stores_attributes(self) -> None:
        """Requirement: all context attributes are accessible."""
        err = DiagramRenderError(
            "arch-diagram",
            "plantuml",
            "web",
            "connection refused",
        )
        assert err.block_name == "arch-diagram"
        assert err.engine == "plantuml"
        assert err.mode == "web"
        assert err.reason == "connection refused"

    def test_args_passed_to_super(self) -> None:
        """Requirement: all args are forwarded to Exception base."""
        err = DiagramRenderError(
            "seq-1",
            "mermaid",
            "offline",
            "mmdc not found",
        )
        assert err.args == ("seq-1", "mermaid", "offline", "mmdc not found")


class TestInvalidMarkdownError:
    """Tests for InvalidMarkdownError."""

    def test_inherits_from_scribpy_error(self) -> None:
        """Requirement: catchable via ScribpyError."""
        assert issubclass(InvalidMarkdownError, ScribpyError)

    def test_stores_detail(self) -> None:
        """Requirement: the structural problem detail is accessible."""
        err = InvalidMarkdownError("missing heading level 1")
        assert err.detail == "missing heading level 1"

    def test_message_contains_detail(self) -> None:
        """Requirement: the error message includes the detail."""
        err = InvalidMarkdownError("empty document")
        assert "empty document" in str(err)
