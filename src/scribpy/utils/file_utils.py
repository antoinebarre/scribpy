"""Markdown file and filesystem utility public facade."""

from __future__ import annotations

from scribpy.utils.filesystem import RealFileSystem
from scribpy.utils.markdown_files import (
    is_md_file,
    list_md_files,
    read_md_file,
    write_md_file,
)

__all__ = [
    "RealFileSystem",
    "is_md_file",
    "list_md_files",
    "read_md_file",
    "write_md_file",
]
