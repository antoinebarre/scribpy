"""Tests for scribpy.errors exception hierarchy."""

import pytest

from scribpy.errors import (
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
