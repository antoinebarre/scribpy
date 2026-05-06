"""Tests for application-level result dataclasses."""

from dataclasses import FrozenInstanceError, is_dataclass
from pathlib import Path

import pytest

from scribpy.model import (
    BuildArtifact,
    BuildResult,
    Diagnostic,
    Document,
    LintResult,
    MarkdownAst,
    ParseResult,
)


def test_result_objects_are_frozen_dataclasses() -> None:
    result_types = (BuildArtifact, BuildResult, LintResult, ParseResult)

    for result_type in result_types:
        assert is_dataclass(result_type)
        assert result_type.__dataclass_params__.frozen is True


def test_lint_result_exposes_diagnostics_and_failure_state() -> None:
    diagnostic = Diagnostic(
        severity="error",
        code="LINT001",
        message="Missing H1 heading",
    )

    result = LintResult(diagnostics=(diagnostic,), failed=True)

    assert result.diagnostics == (diagnostic,)
    assert result.failed is True

    with pytest.raises(FrozenInstanceError):
        result.failed = False


def test_parse_result_exposes_documents_diagnostics_and_failure_state() -> None:
    document = Document(
        path=Path("doc/index.md"),
        relative_path=Path("index.md"),
        source="# Title\n",
        frontmatter={"title": "Title"},
        ast=MarkdownAst(backend="scribpy-minimal", tokens=()),
        title="Title",
        headings=(),
        links=(),
        assets=(),
    )
    diagnostic = Diagnostic(
        severity="error",
        code="PRS002",
        message="Invalid frontmatter",
    )

    result = ParseResult(
        documents=(document,),
        diagnostics=(diagnostic,),
        failed=True,
    )

    assert result.documents == (document,)
    assert result.diagnostics == (diagnostic,)
    assert result.failed is True

    with pytest.raises(FrozenInstanceError):
        result.failed = False


def test_build_artifact_captures_path_target_type_and_metadata() -> None:
    artifact = BuildArtifact(
        path=Path("build/html/index.html"),
        target="html",
        artifact_type="page",
        metadata={"content_type": "text/html", "bytes": 2048},
    )

    assert artifact.path == Path("build/html/index.html")
    assert artifact.target == "html"
    assert artifact.artifact_type == "page"
    assert artifact.metadata == {"content_type": "text/html", "bytes": 2048}


def test_successful_build_result_can_report_artifacts_and_diagnostics() -> None:
    artifact = BuildArtifact(
        path=Path("build/markdown/document.md"),
        target="markdown",
        artifact_type="document",
    )
    diagnostic = Diagnostic(
        severity="info",
        code="BUILD001",
        message="Markdown artifact created",
    )

    result = BuildResult(
        success=True,
        artifacts=(artifact,),
        diagnostics=(diagnostic,),
    )

    assert result.success is True
    assert result.artifacts == (artifact,)
    assert result.diagnostics == (diagnostic,)


def test_failed_build_result_can_report_diagnostics_without_artifacts() -> None:
    diagnostic = Diagnostic(
        severity="error",
        code="BUILD002",
        message="PDF renderer is unavailable",
        hint="Install the optional PDF dependencies.",
    )

    result = BuildResult(
        success=False,
        artifacts=(),
        diagnostics=(diagnostic,),
    )

    assert result.success is False
    assert result.artifacts == ()
    assert result.diagnostics == (diagnostic,)
