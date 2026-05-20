"""Tests for compact CLI execution reports."""

from io import StringIO
from pathlib import Path

from scribpy.cli.reporting import print_build_report
from scribpy.model import BuildArtifact, BuildResult


def test_build_report_omits_artifact_summary_when_none_exist() -> None:
    stream = StringIO()

    print_build_report(
        BuildResult(success=True, artifacts=(), diagnostics=()),
        "Markdown",
        stream,
    )

    assert "Primary artifact:" not in stream.getvalue()


def test_build_report_falls_back_to_first_artifact_when_no_preferred_type() -> (
    None
):
    stream = StringIO()

    print_build_report(
        BuildResult(
            success=True,
            artifacts=(BuildArtifact(Path("asset.bin"), "assets", "binary"),),
            diagnostics=(),
        ),
        "Assets",
        stream,
    )

    assert "Primary artifact: asset.bin" in stream.getvalue()
