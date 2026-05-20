"""Tests for asset renderers and image file helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scribpy.report.assets import AssetRenderer, MatplotlibRenderer, copy_image_file


class TestAssetRendererProtocol:
    def test_matplotlib_renderer_satisfies_protocol(self, tmp_path):
        fig = _make_mock_figure()
        renderer = MatplotlibRenderer(fig)
        assert isinstance(renderer, AssetRenderer)

    def test_arbitrary_object_without_render_fails_protocol(self):
        assert not isinstance(object(), AssetRenderer)


class TestMatplotlibRenderer:
    def test_render_calls_savefig(self, tmp_path):
        fig = _make_mock_figure()
        renderer = MatplotlibRenderer(fig, dpi=100)
        out = str(tmp_path / "chart.png")
        result = renderer.render(out)
        fig.savefig.assert_called_once_with(out, dpi=100, bbox_inches="tight")
        assert result == out

    def test_render_creates_parent_dirs(self, tmp_path):
        fig = _make_mock_figure()
        renderer = MatplotlibRenderer(fig)
        out = str(tmp_path / "deep" / "dir" / "chart.png")
        renderer.render(out)
        assert Path(out).parent.exists()

    def test_default_dpi_is_150(self, tmp_path):
        fig = _make_mock_figure()
        renderer = MatplotlibRenderer(fig)
        out = str(tmp_path / "chart.png")
        renderer.render(out)
        _, kwargs = fig.savefig.call_args
        assert kwargs["dpi"] == 150

    def test_render_returns_output_path(self, tmp_path):
        fig = _make_mock_figure()
        renderer = MatplotlibRenderer(fig)
        out = str(tmp_path / "chart.png")
        assert renderer.render(out) == out


class TestCopyImageFile:
    def test_copies_file_to_assets_dir(self, tmp_path):
        src = tmp_path / "photo.png"
        src.write_bytes(b"\x89PNG")
        assets_dir = tmp_path / "out" / "assets"
        result = copy_image_file(str(src), assets_dir)
        assert (assets_dir / "photo.png").exists()
        assert result == "assets/photo.png"

    def test_creates_assets_dir_if_missing(self, tmp_path):
        src = tmp_path / "img.jpg"
        src.write_bytes(b"JFIF")
        assets_dir = tmp_path / "new" / "assets"
        copy_image_file(str(src), assets_dir)
        assert assets_dir.exists()

    def test_returns_posix_relative_path(self, tmp_path):
        src = tmp_path / "logo.svg"
        src.write_bytes(b"<svg/>")
        assets_dir = tmp_path / "assets"
        result = copy_image_file(str(src), assets_dir)
        assert "/" in result
        assert result == "assets/logo.svg"

    def test_missing_source_raises(self, tmp_path):
        assets_dir = tmp_path / "assets"
        with pytest.raises(FileNotFoundError):
            copy_image_file(str(tmp_path / "nonexistent.png"), assets_dir)


def _make_mock_figure() -> MagicMock:
    """Return a MagicMock that satisfies _SavableFigure."""
    fig = MagicMock()
    fig.savefig = MagicMock()
    return fig
