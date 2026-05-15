"""Tests for shared project-pipeline behavior."""

from pathlib import Path

from scribpy.core.project_pipeline import run_project_parse_pipeline


def test_project_pipeline_preserves_documents_on_parse_failure(tmp_path: Path) -> None:
    (tmp_path / "scribpy.toml").write_text('[paths]\nsource = "doc"\n', encoding="utf-8")
    source = tmp_path / "doc/index.md"
    source.parent.mkdir()
    source.write_text("# Home\n", encoding="utf-8")

    class FailingParser:
        def parse(self, text: str):
            raise RuntimeError("boom")

    result = run_project_parse_pipeline(tmp_path, parser=FailingParser())

    assert result.failed is True
    assert result.value is not None
    assert result.value.documents == ()
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["PRS003"]
