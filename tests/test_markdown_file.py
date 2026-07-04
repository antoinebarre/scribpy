"""Tests for the MarkdownFile domain object."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import mkforge
import pytest

from scribpy.core import MarkdownDocument, MarkdownFile, MarkdownImageReference


class TestMarkdownFileCreation:
    """Tests for MarkdownFile creation."""

    def test_from_text_stores_path_content_and_encoding(self) -> None:
        """Requirement: MarkdownFile stores source text and file metadata."""
        markdown = MarkdownFile(
            path=Path("docs/index.md"),
            content="# Title\n",
            encoding="utf-8",
        )

        assert markdown.path == Path("docs/index.md")
        assert markdown.content == "# Title\n"
        assert markdown.encoding == "utf-8"

    def test_from_path_reads_markdown_file(self, tmp_path: Path) -> None:
        """Requirement: MarkdownFile can load a Markdown file from disk."""
        source_path = tmp_path / "index.md"
        source_path.write_text("# Title\n", encoding="utf-8")

        markdown = MarkdownFile.from_path(source_path)

        assert markdown.path == source_path
        assert markdown.content == "# Title\n"

    def test_name_returns_path_name(self) -> None:
        """Requirement: MarkdownFile exposes the source file name."""
        markdown = MarkdownFile(Path("docs/index.md"), "# Title\n")

        assert markdown.name == "index.md"

    def test_suffix_returns_path_suffix(self) -> None:
        """Requirement: MarkdownFile exposes the source file suffix."""
        markdown = MarkdownFile(Path("docs/index.md"), "# Title\n")

        assert markdown.suffix == ".md"


class TestMarkdownFileModification:
    """Tests for immutable MarkdownFile modification helpers."""

    def test_with_content_returns_updated_copy(self) -> None:
        """Requirement: content replacement keeps the source object intact."""
        original = MarkdownFile(Path("index.md"), "# Old\n")

        updated = original.with_content("# New\n")

        assert original.content == "# Old\n"
        assert updated.content == "# New\n"
        assert updated.path == original.path

    def test_replace_text_returns_updated_copy(self) -> None:
        """Requirement: text replacement keeps the source object intact."""
        original = MarkdownFile(Path("index.md"), "# Old\nOld body\n")

        updated = original.replace_text("Old", "New")

        assert original.content == "# Old\nOld body\n"
        assert updated.content == "# New\nNew body\n"

    def test_to_document_returns_markdown_document(self) -> None:
        """Requirement: MarkdownFile creates an in-memory document."""
        markdown = MarkdownFile(Path("index.md"), "![Logo](logo.png)\n")

        document = markdown.to_document()

        assert document == MarkdownDocument("![Logo](logo.png)\n")
        assert document.image_references == (
            MarkdownImageReference(
                alt_text="Logo",
                target="logo.png",
                title=None,
                line=1,
                column=1,
            ),
        )

    def test_write_uses_current_path_when_destination_is_omitted(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: MarkdownFile can write content to its own path."""
        destination = tmp_path / "index.md"
        markdown = MarkdownFile(destination, "# Title\n")

        written_path = markdown.write()

        assert written_path == destination
        assert destination.read_text(encoding="utf-8") == "# Title\n"

    def test_write_uses_explicit_destination(self, tmp_path: Path) -> None:
        """Requirement: MarkdownFile can write to another destination."""
        destination = tmp_path / "nested" / "copy.md"
        markdown = MarkdownFile(Path("index.md"), "# Title\n")

        written_path = markdown.write(destination)

        assert written_path == destination
        assert destination.read_text(encoding="utf-8") == "# Title\n"


class TestMarkdownFileMkforgeAdapter:
    """Tests for MarkdownFile delegation to mkforge."""

    def test_verify_delegates_to_mkforge(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Requirement: Markdown verification is delegated to mkforge."""
        calls: dict[str, object] = {}
        expected_report = mkforge.VerificationReport("rules", ())

        def fake_verify_markdown(
            source: str,
            *,
            source_path: Path,
            settings: mkforge.VerificationSettings | None,
            custom_rules: object,
        ) -> mkforge.VerificationReport:
            """Record a mkforge verification call.

            Args:
                source: Markdown source passed by Scribpy.
                source_path: Markdown source path passed by Scribpy.
                settings: Verification settings passed by Scribpy.
                custom_rules: Custom rules passed by Scribpy.

            Returns:
                Expected verification report.
            """
            calls["source"] = source
            calls["source_path"] = source_path
            calls["settings"] = settings
            calls["custom_rules"] = custom_rules
            return expected_report

        monkeypatch.setattr(mkforge, "verify_markdown", fake_verify_markdown)
        markdown = MarkdownFile(Path("index.md"), "# Title\n")

        report = markdown.verify()

        assert report is expected_report
        assert calls == {
            "source": "# Title\n",
            "source_path": Path("index.md"),
            "settings": None,
            "custom_rules": (),
        }

    def test_has_valid_images_delegates_to_mkforge(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Requirement: image validation is delegated to mkforge."""
        calls: dict[str, object] = {}

        def fake_validate_markdown_images(
            markdown: str,
            *,
            base_path: Path,
            timeout: float,
        ) -> bool:
            """Record a mkforge image validation call.

            Args:
                markdown: Markdown source passed by Scribpy.
                base_path: Base path passed by Scribpy.
                timeout: Timeout passed by Scribpy.

            Returns:
                True to signal valid images.
            """
            calls["markdown"] = markdown
            calls["base_path"] = base_path
            calls["timeout"] = timeout
            return True

        monkeypatch.setattr(
            mkforge,
            "validate_markdown_images",
            fake_validate_markdown_images,
        )
        markdown = MarkdownFile(Path("index.md"), "# Title\n")

        assert markdown.has_valid_images(timeout=1.5) is True
        assert calls == {
            "markdown": "# Title\n",
            "base_path": Path("index.md"),
            "timeout": 1.5,
        }

    def test_has_expected_headings_delegates_to_mkforge(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Requirement: heading validation is delegated to mkforge."""
        calls: dict[str, object] = {}

        def fake_validate_markdown_headings(
            markdown: str,
            expected: object,
            *,
            strict: bool,
        ) -> bool:
            """Record a mkforge heading validation call.

            Args:
                markdown: Markdown source passed by Scribpy.
                expected: Expected headings passed by Scribpy.
                strict: Strict mode passed by Scribpy.

            Returns:
                True to signal valid headings.
            """
            calls["markdown"] = markdown
            calls["expected"] = expected
            calls["strict"] = strict
            return True

        monkeypatch.setattr(
            mkforge,
            "validate_markdown_headings",
            fake_validate_markdown_headings,
        )
        markdown = MarkdownFile(Path("index.md"), "# Title\n")
        expected = ((1, "Title"),)

        assert markdown.has_expected_headings(expected, strict=True) is True
        assert calls == {
            "markdown": "# Title\n",
            "expected": expected,
            "strict": True,
        }

    def test_has_expected_yaml_delegates_to_mkforge(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Requirement: YAML validation is delegated to mkforge."""
        calls: dict[str, object] = {}

        def fake_validate_markdown_yaml(
            markdown: str,
            expected: Mapping[str, object],
            *,
            strict: bool,
        ) -> bool:
            """Record a mkforge YAML validation call.

            Args:
                markdown: Markdown source passed by Scribpy.
                expected: Expected YAML values passed by Scribpy.
                strict: Strict mode passed by Scribpy.

            Returns:
                True to signal valid YAML front matter.
            """
            calls["markdown"] = markdown
            calls["expected"] = expected
            calls["strict"] = strict
            return True

        monkeypatch.setattr(
            mkforge,
            "validate_markdown_yaml",
            fake_validate_markdown_yaml,
        )
        markdown = MarkdownFile(Path("i.md"), "---\ntitle: Home\n---\n")
        expected = {"title": "Home"}

        assert markdown.has_expected_yaml(expected, strict=True) is True
        assert calls == {
            "markdown": "---\ntitle: Home\n---\n",
            "expected": expected,
            "strict": True,
        }
