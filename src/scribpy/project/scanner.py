"""Project source discovery for Scribpy documentation projects."""

from __future__ import annotations

from pathlib import Path

from scribpy.config import Config
from scribpy.model import Diagnostic, SourceFile
from scribpy.utils.file_utils import list_md_files


def resolve_project_root(config_path: Path) -> Path:
    """Resolve the project root from a ``scribpy.toml`` path.

    Args:
        config_path: Path to the project configuration file.

    Returns:
        Absolute project root path, defined as the configuration file parent.
    """
    return config_path.resolve().parent


def scan_project(
    root: Path,
    config: Config,
) -> tuple[tuple[SourceFile, ...], tuple[Diagnostic, ...]]:
    """Discover Markdown source files for a configured project.

    Args:
        root: Project root directory.
        config: Parsed Scribpy configuration.

    Returns:
        A tuple containing discovered source files and user-facing diagnostics.
        Source file paths are ordered deterministically and their relative paths
        are relative to the configured source directory.
    """
    project_root = root.resolve()
    source_dir = (project_root / config.paths.source).resolve()

    if not _is_relative_to(source_dir, project_root):
        return (), (
            Diagnostic(
                severity="error",
                code="PRJ003",
                message="Configured source path must stay inside the project.",
                path=config.paths.source,
                hint="Use a source path relative to the project root.",
            ),
        )

    if not source_dir.is_dir():
        return (), (
            Diagnostic(
                severity="error",
                code="PRJ001",
                message="Configured source directory does not exist.",
                path=config.paths.source,
                hint="Create the source directory or update paths.source.",
            ),
        )

    source_paths = sorted(
        list_md_files(source_dir, recursive=True),
        key=lambda path: path.relative_to(source_dir).as_posix(),
    )
    if not source_paths:
        return (), (
            Diagnostic(
                severity="warning",
                code="PRJ002",
                message="No Markdown source files found.",
                path=config.paths.source,
                hint="Add at least one .md file under the source directory.",
            ),
        )

    source_files = tuple(
        SourceFile(path=path, relative_path=path.relative_to(source_dir))
        for path in source_paths
    )
    return source_files, ()


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


__all__ = ["resolve_project_root", "scan_project"]
