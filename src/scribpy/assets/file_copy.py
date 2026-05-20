"""Copy referenced local assets into build output directories."""

from __future__ import annotations

from pathlib import Path

from scribpy.model import BuildArtifact, Diagnostic
from scribpy.model.protocols import FileSystem


def copy_assets(
    asset_paths: tuple[Path, ...],
    source_root: Path,
    dest_dir: Path,
    filesystem: FileSystem,
) -> tuple[tuple[BuildArtifact, ...], tuple[Diagnostic, ...]]:
    """Copy asset files to a destination directory, preserving structure.

    Args:
        asset_paths: Absolute asset paths to copy.
        source_root: Absolute source root to compute relative sub-paths.
        dest_dir: Absolute destination directory.
        filesystem: Filesystem service used for reading and writing.

    Returns:
        Produced artifacts plus copy diagnostics.
    """
    artifacts: list[BuildArtifact] = []
    diagnostics: list[Diagnostic] = []

    for abs_path in asset_paths:
        if not filesystem.exists(abs_path):
            diagnostics.append(_missing_asset_diagnostic(abs_path))
            continue
        dest = dest_dir / _relative_asset_path(abs_path, source_root)
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            content = filesystem.read_text(abs_path)
            filesystem.write_text(dest, content)
        except Exception as exc:
            diagnostics.append(_copy_failure_diagnostic(abs_path, dest, exc))
            continue
        artifacts.append(
            BuildArtifact(path=dest, target="assets", artifact_type="image")
        )

    return tuple(artifacts), tuple(diagnostics)


def _relative_asset_path(abs_path: Path, source_root: Path) -> Path:
    """Return the destination-relative path for one copied asset."""
    try:
        return abs_path.relative_to(source_root)
    except ValueError:
        return Path(abs_path.name)


def _missing_asset_diagnostic(path: Path) -> Diagnostic:
    """Return a warning diagnostic for a missing referenced asset."""
    return Diagnostic(
        severity="warning",
        code="ASS001",
        message=f"Asset not found, skipping copy: {path}",
        path=path,
        hint="Ensure the asset file exists at the referenced path.",
    )


def _copy_failure_diagnostic(
    source: Path, dest: Path, exc: Exception
) -> Diagnostic:
    """Return an error diagnostic for a failed asset copy."""
    return Diagnostic(
        severity="error",
        code="ASS002",
        message=f"Cannot copy asset {source.name}: {exc}",
        path=dest,
        hint="Check that the asset destination is writable.",
    )


__all__ = ["copy_assets"]
