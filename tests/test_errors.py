"""Tests for scribpy.errors exception hierarchy."""

import pytest

from scribpy.errors import (
    InvalidMarkdownError,
    InvalidScribpyManifestError,
    ScribpyError,
    ScribpyManifestWarning,
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


class TestInvalidScribpyManifestError:
    """Tests for InvalidScribpyManifestError."""

    def test_inherits_from_scribpy_error(self) -> None:
        """Requirement: manifest errors are catchable via ScribpyError."""
        assert issubclass(InvalidScribpyManifestError, ScribpyError)

    def test_stores_path_and_detail(self) -> None:
        """Requirement: manifest error context is accessible."""
        err = InvalidScribpyManifestError("docs/scribpy.yml", "bad order")

        assert err.path == "docs/scribpy.yml"
        assert err.detail == "bad order"

    def test_message_contains_path_and_detail(self) -> None:
        """Requirement: manifest errors name the manifest and problem."""
        err = InvalidScribpyManifestError("docs/scribpy.yml", "bad order")

        assert "docs/scribpy.yml" in str(err)
        assert "bad order" in str(err)
        assert err.args == ("docs/scribpy.yml", "bad order")


class TestScribpyManifestWarning:
    """Tests for ScribpyManifestWarning."""

    def test_is_user_warning(self) -> None:
        """Requirement: manifest warnings are standard user warnings."""
        assert issubclass(ScribpyManifestWarning, UserWarning)
