"""Tests for scribpy.utils.file_utils."""

from pathlib import Path

import pytest

from scribpy.utils import is_md_file, list_md_files, read_md_file, write_md_file

# --- is_md_file ---


def test_is_md_file_returns_true_for_existing_md(tmp_path: Path) -> None:
    f = tmp_path / "doc.md"
    f.write_text("# Hello")
    assert is_md_file(f) is True


def test_is_md_file_returns_false_for_wrong_extension(tmp_path: Path) -> None:
    f = tmp_path / "doc.txt"
    f.write_text("hello")
    assert is_md_file(f) is False


def test_is_md_file_returns_false_for_nonexistent_path() -> None:
    assert is_md_file(Path("/nonexistent/file.md")) is False


def test_is_md_file_returns_false_for_directory(tmp_path: Path) -> None:
    assert is_md_file(tmp_path) is False


def test_is_md_file_is_case_insensitive(tmp_path: Path) -> None:
    f = tmp_path / "doc.MD"
    f.write_text("# Hello")
    assert is_md_file(f) is True


# --- list_md_files ---


def test_list_md_files_returns_md_files_recursive(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("# A")
    (tmp_path / "b.txt").write_text("not md")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.md").write_text("# C")

    result = list_md_files(tmp_path, recursive=True)

    assert result == sorted([tmp_path / "a.md", sub / "c.md"])


def test_list_md_files_non_recursive_skips_subdirectories(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("# A")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.md").write_text("# C")

    result = list_md_files(tmp_path, recursive=False)

    assert result == [tmp_path / "a.md"]


def test_list_md_files_returns_empty_for_no_md_files(tmp_path: Path) -> None:
    (tmp_path / "readme.txt").write_text("text")
    assert list_md_files(tmp_path) == []


def test_list_md_files_raises_for_non_directory(tmp_path: Path) -> None:
    f = tmp_path / "file.md"
    f.write_text("# A")
    with pytest.raises(NotADirectoryError):
        list_md_files(f)


def test_list_md_files_result_is_sorted(tmp_path: Path) -> None:
    (tmp_path / "z.md").write_text("")
    (tmp_path / "a.md").write_text("")
    (tmp_path / "m.md").write_text("")

    result = list_md_files(tmp_path)

    assert result == sorted(result)


# --- read_md_file ---


def test_read_md_file_returns_content(tmp_path: Path) -> None:
    f = tmp_path / "doc.md"
    f.write_text("# Title\n\nBody text.", encoding="utf-8")
    assert read_md_file(f) == "# Title\n\nBody text."


def test_read_md_file_raises_for_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        read_md_file(tmp_path / "missing.md")


def test_read_md_file_raises_for_wrong_extension(tmp_path: Path) -> None:
    f = tmp_path / "doc.txt"
    f.write_text("hello")
    with pytest.raises(ValueError):
        read_md_file(f)


# --- write_md_file ---


def test_write_md_file_creates_file(tmp_path: Path) -> None:
    f = tmp_path / "out.md"
    write_md_file(f, "# New doc")
    assert f.read_text(encoding="utf-8") == "# New doc"


def test_write_md_file_overwrites_existing(tmp_path: Path) -> None:
    f = tmp_path / "out.md"
    f.write_text("old")
    write_md_file(f, "new content")
    assert f.read_text(encoding="utf-8") == "new content"


def test_write_md_file_creates_parents_when_requested(tmp_path: Path) -> None:
    f = tmp_path / "sub" / "nested" / "out.md"
    write_md_file(f, "# Nested", create_parents=True)
    assert f.read_text(encoding="utf-8") == "# Nested"


def test_write_md_file_raises_when_parent_missing(tmp_path: Path) -> None:
    f = tmp_path / "missing_dir" / "out.md"
    with pytest.raises(FileNotFoundError):
        write_md_file(f, "# Hello")


def test_write_md_file_raises_for_wrong_extension(tmp_path: Path) -> None:
    f = tmp_path / "out.txt"
    with pytest.raises(ValueError):
        write_md_file(f, "# Hello")
