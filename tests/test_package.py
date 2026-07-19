"""Tests for the scribpy top-level package."""

import scribpy


class TestPublicApi:
    """Tests for public exports from scribpy.__init__."""

    def test_version_is_string(self) -> None:
        """Requirement: __version__ is a non-empty string."""
        assert isinstance(scribpy.__version__, str)
        assert len(scribpy.__version__) > 0

    def test_all_exports_are_importable(self) -> None:
        """Requirement: every name in __all__ is importable."""
        for name in scribpy.__all__:
            assert hasattr(scribpy, name), f"{name} not importable"
