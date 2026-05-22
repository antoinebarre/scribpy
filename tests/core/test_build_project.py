"""Tests for build_project (phase 5)."""

from pathlib import Path

from scribpy.core import build_project


def _write_config(root: Path, content: str) -> None:
    (root / "scribpy.toml").write_text(content, encoding="utf-8")


def _write_source(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_build_project_writes_markdown_in_explicit_index_order(
    tmp_path: Path,
) -> None:
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


def test_build_project_stops_before_writing_when_lint_fails(
    tmp_path: Path,
) -> None:
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


def test_build_project_stops_when_project_preparation_fails(
    tmp_path: Path,
) -> None:
    result = build_project(tmp_path)

    assert result.success is False
    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "CFG001",
        "BLD002",
    ]


def test_build_project_rejects_unknown_target(tmp_path: Path) -> None:
    result = build_project(tmp_path, target="docx")

    assert result.success is False
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["BLD001"]


def test_build_project_stops_when_transform_reports_error(
    tmp_path: Path,
) -> None:
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
        registry=ExtensionRegistry.native().with_markdown_transform(
            failing_transform
        ),
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


def test_build_project_uses_document_transform_configuration(
    tmp_path: Path,
) -> None:
    _write_config(
        tmp_path,
        '[project]\nname = "Project Name"\n\n'
        '[paths]\nsource = "doc"\n\n'
        '[document]\ntitle = "Configured Manual"\n\n'
        "[document.toc]\nenabled = false\n\n"
        '[document.numbering]\nstyle = "roman"\nmax_level = 2\n',
    )
    _write_source(tmp_path, "doc/index.md", "# Home\n\n## Setup\n")

    result = build_project(tmp_path)

    assert result.success is True
    assert result.artifacts[0].path.read_text(encoding="utf-8") == (
        "# Configured Manual\n\n## I Home\n\n### Setup\n"
    )


def test_build_project_pdf_uses_injected_renderer_and_css(
    tmp_path: Path,
) -> None:
    from scribpy.builders.pdf import PdfDocument, PdfRenderResult
    from scribpy.model import BuildArtifact

    _write_config(
        tmp_path,
        '[paths]\nsource = "doc"\n\n[builders.pdf]\ncss = ["theme/pdf.css"]\n',
    )
    _write_source(
        tmp_path, "doc/index.md", "# Home\n\n![Logo](assets/logo.svg)\n"
    )
    _write_source(tmp_path, "doc/assets/logo.svg", "<svg/>\n")
    _write_source(tmp_path, "theme/pdf.css", "h1 { color: teal; }\n")
    seen: list[PdfDocument] = []

    class FakePdfRenderer:
        def render(
            self, document: PdfDocument, output_path: Path
        ) -> PdfRenderResult:
            seen.append(document)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"%PDF-FAKE")
            return PdfRenderResult(
                artifact=BuildArtifact(
                    path=output_path,
                    target="pdf",
                    artifact_type="document",
                )
            )

    from scribpy.core.build_options import PdfBuildOverrides
    from scribpy.core.build_project import build_pdf_with_overrides

    result = build_pdf_with_overrides(
        tmp_path,
        PdfBuildOverrides(extra_css=(Path("theme/pdf.css"),)),
        pdf_renderer=FakePdfRenderer(),
    )

    assert result.success is True
    assert result.artifacts[0].path == tmp_path / "build/pdf/document.pdf"
    assert (tmp_path / "build/pdf/assets/assets/logo.svg").is_file()
    assert seen[0].root == (tmp_path / "build/pdf").resolve()
    assert seen[0].css_files == (
        tmp_path / "theme/pdf.css",
        tmp_path / "theme/pdf.css",
    )
    assert "![Logo](assets/assets/logo.svg)" in seen[0].markdown


def test_build_project_pdf_reports_missing_css(tmp_path: Path) -> None:
    _write_config(
        tmp_path,
        '[paths]\nsource = "doc"\n\n[builders.pdf]\ncss = ["missing.css"]\n',
    )
    _write_source(tmp_path, "doc/index.md", "# Home\n")

    result = build_project(tmp_path, target="pdf")

    assert result.success is False
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["PDF003"]


def test_pdf_link_replacement_preserves_external_links() -> None:
    from scribpy.core.build_pdf import _MARKDOWN_LINK_RE, _pdf_link_replacement

    external = _MARKDOWN_LINK_RE.search("[Site](https://example.test)")
    internal = _MARKDOWN_LINK_RE.search("[Guide](guide/page.md)")

    assert external is not None
    assert internal is not None
    assert _pdf_link_replacement(external) == "[Site](https://example.test)"
    assert _pdf_link_replacement(internal) == "Guide"


def test_build_project_pdf_stops_when_project_preparation_fails(
    tmp_path: Path,
) -> None:
    result = build_project(tmp_path, target="pdf")

    assert result.success is False
    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "CFG001",
        "BLD002",
    ]


def test_build_pdf_project_stops_when_project_preparation_fails(
    tmp_path: Path,
) -> None:
    from scribpy.config.types import PdfBuilderConfig
    from scribpy.core.build_pdf import build_pdf_project

    result = build_pdf_project(
        tmp_path,
        pdf_config=PdfBuilderConfig(),
        filesystem=None,
        parser=None,
        registry=None,
    )

    assert result.success is False
    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "CFG001",
        "BLD002",
    ]


def test_build_pdf_project_stops_when_lint_fails(tmp_path: Path) -> None:
    from scribpy.config.types import PdfBuilderConfig
    from scribpy.core.build_pdf import build_pdf_project

    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "## Missing H1\n")

    result = build_pdf_project(
        tmp_path,
        pdf_config=PdfBuilderConfig(),
        filesystem=None,
        parser=None,
        registry=None,
    )

    assert result.success is False
    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "LINT001",
        "LINT002",
        "BLD002",
    ]


def test_build_pdf_project_stops_when_transform_reports_error(
    tmp_path: Path,
) -> None:
    from scribpy.config.types import PdfBuilderConfig
    from scribpy.core.build_pdf import build_pdf_project
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

    result = build_pdf_project(
        tmp_path,
        pdf_config=PdfBuilderConfig(),
        filesystem=None,
        parser=None,
        registry=ExtensionRegistry.native().with_markdown_transform(
            failing_transform
        ),
    )

    assert result.success is False
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["TRN001"]


def test_build_pdf_project_reports_asset_copy_error(tmp_path: Path) -> None:
    from scribpy.config.types import PdfBuilderConfig
    from scribpy.core.build_pdf import build_pdf_project
    from scribpy.utils.file_utils import RealFileSystem

    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "# Home\n\n![Logo](logo.svg)\n")
    _write_source(tmp_path, "doc/logo.svg", "<svg/>\n")

    class FailingAssetWriteFileSystem(RealFileSystem):
        def write_text(self, path: Path, content: str) -> None:
            if path.name == "logo.svg":
                raise OSError("read-only")
            super().write_text(path, content)

    result = build_pdf_project(
        tmp_path,
        pdf_config=PdfBuilderConfig(),
        filesystem=FailingAssetWriteFileSystem(),
        parser=None,
        registry=None,
    )

    assert result.success is False
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["ASS002"]
