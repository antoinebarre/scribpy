"""Copy configured CSS files for single-page HTML output."""

from __future__ import annotations

from pathlib import Path

from scribpy.model import BuildArtifact, Diagnostic
from scribpy.model.protocols import FileSystem


def copy_css_files_single_page(
    project_root: Path,
    css_sources: tuple[Path, ...],
    output_dir: Path,
    filesystem: FileSystem,
) -> tuple[tuple[BuildArtifact, ...], tuple[Diagnostic, ...], list[str]]:
    """Copy CSS files into the single-page output directory.

    Args:
        project_root: Absolute project root directory.
        css_sources: CSS file paths relative to the project root.
        output_dir: Absolute single-page output directory.
        filesystem: Filesystem service.

    Returns:
        Artifacts, diagnostics, and CSS hrefs relative to ``index.html``.
    """
    artifacts: list[BuildArtifact] = []
    hrefs: list[str] = []
    css_dir = output_dir / "css"

    for css_source in css_sources:
        abs_source = project_root / css_source
        if not filesystem.exists(abs_source):
            return (), (_missing_css_diagnostic(css_source, abs_source),), []
        dest = css_dir / css_source.name
        try:
            css_dir.mkdir(parents=True, exist_ok=True)
            content = filesystem.read_text(abs_source)
            filesystem.write_text(dest, content)
        except Exception as exc:
            return (), (_copy_css_diagnostic(css_source, dest, exc),), []
        artifacts.append(
            BuildArtifact(path=dest, target="html", artifact_type="stylesheet")
        )
        hrefs.append(f"css/{css_source.name}")

    return tuple(artifacts), (), hrefs


def _missing_css_diagnostic(css_source: Path, abs_source: Path) -> Diagnostic:
    """Return a diagnostic for a missing configured CSS file."""
    return Diagnostic(
        severity="error",
        code="CSS001",
        message=f"CSS file not found: {css_source}",
        path=abs_source,
        hint=(
            "Check that the css_files path is relative to the project root."
        ),
    )


def _copy_css_diagnostic(
    css_source: Path, dest: Path, exc: Exception
) -> Diagnostic:
    """Return a diagnostic for a failed configured CSS copy."""
    return Diagnostic(
        severity="error",
        code="CSS002",
        message=f"Cannot copy CSS file {css_source.name}: {exc}",
        path=dest,
        hint="Check that the css directory is writable.",
    )


__all__ = ["copy_css_files_single_page"]
