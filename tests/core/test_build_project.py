"""Tests for build_project (phase 5)."""

from pathlib import Path

from scribpy.core import build_project


def _write_config(root: Path, content: str) -> None:
    (root / "scribpy.toml").write_text(content, encoding="utf-8")


def _write_source(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_build_project_writes_markdown_in_explicit_index_order(tmp_path: Path) -> None:
    _write_config(
        tmp_path,
        '[paths]\nsource = "doc"\n\n[index]\nmode = "explicit"\nfiles = ["b.md", "a.md"]\n',
    )
    _write_source(tmp_path, "doc/a.md", "# A\n")
    _write_source(tmp_path, "doc/b.md", "# B\n")

    result = build_project(tmp_path)

    assert result.success is True
    assert result.diagnostics == ()
    assert len(result.artifacts) == 1
    artifact = result.artifacts[0]
    assert artifact.path == tmp_path / "build/markdown/document.md"
    assert artifact.path.read_text(encoding="utf-8") == (
        "# Document\n\n"
        "## Table of Contents\n"
        "- [1 B](#1-b)\n"
        "- [2 A](#2-a)\n\n"
        "## 1 B\n\n"
        "## 2 A\n"
    )


def test_build_project_stops_before_writing_when_lint_fails(tmp_path: Path) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "## Missing H1\n")

    result = build_project(tmp_path)

    assert result.success is False
    assert result.artifacts == ()
    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "LINT001",
        "LINT002",
        "BLD002",
    ]
    assert not (tmp_path / "build/markdown/document.md").exists()


def test_build_project_stops_when_project_preparation_fails(tmp_path: Path) -> None:
    result = build_project(tmp_path)

    assert result.success is False
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["CFG001", "BLD002"]


def test_build_project_rejects_unknown_target(tmp_path: Path) -> None:
    result = build_project(tmp_path, target="html")

    assert result.success is False
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["BLD001"]


def test_build_project_stops_when_transform_reports_error(tmp_path: Path) -> None:
    from scribpy.extensions import ExtensionRegistry
    from scribpy.model import Diagnostic
    from scribpy.transforms import TransformResult

    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "# Home\n")

    def failing_transform(context):
        return TransformResult(
            documents=context.transformed_documents,
            diagnostics=(
                Diagnostic(
                    severity="error",
                    code="TRN001",
                    message="Transform failed.",
                ),
            ),
        )

    result = build_project(
        tmp_path,
        registry=ExtensionRegistry.native().with_markdown_transform(failing_transform),
    )

    assert result.success is False
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["TRN001"]


def test_build_project_reports_artifact_write_failure(tmp_path: Path) -> None:
    from scribpy.utils.file_utils import RealFileSystem

    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "# Home\n")

    class FailingWriteFileSystem(RealFileSystem):
        def write_text(self, path: Path, content: str) -> None:
            raise OSError("read-only")

    result = build_project(tmp_path, filesystem=FailingWriteFileSystem())

    assert result.success is False
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["BLD003"]
