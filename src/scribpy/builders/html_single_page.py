"""Single-page HTML builder — artifact writing and public re-exports."""

from __future__ import annotations

from pathlib import Path

from scribpy.builders.html_inline_renderer import render_markdown_to_html
from scribpy.builders.html_scaffold import build_single_page_html
from scribpy.model import BuildArtifact, Diagnostic
from scribpy.model.protocols import FileSystem

_HTML_OUTPUT_PATH = Path("index.html")
_SCRIPT_OUTPUT_PATH = Path("js/toc.js")


def write_single_page_artifact(
    project_root: Path,
    html: str,
    output_dir: Path,
    filesystem: FileSystem,
) -> tuple[BuildArtifact | None, tuple[Diagnostic, ...]]:
    """Write the single-page HTML artifact to disk.

    Args:
        project_root: Absolute project root directory.
        html: Complete HTML document content.
        output_dir: Relative output directory (e.g. ``build/html``).
        filesystem: Filesystem service used for writing.

    Returns:
        Artifact descriptor on success, plus any write diagnostics.
    """
    artifact_path = project_root / output_dir / _HTML_OUTPUT_PATH
    try:
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        filesystem.write_text(artifact_path, html)
    except Exception as exc:
        return None, (
            Diagnostic(
                severity="error",
                code="BLD005",
                message=f"Cannot write HTML artifact: {exc}",
                path=artifact_path,
                hint="Check that the build directory is writable.",
            ),
        )
    return (
        BuildArtifact(
            path=artifact_path, target="html", artifact_type="document"
        ),
        (),
    )


def write_single_page_script_artifact(
    project_root: Path,
    output_dir: Path,
    filesystem: FileSystem,
) -> tuple[BuildArtifact | None, tuple[Diagnostic, ...]]:
    """Write the JavaScript used by the interactive single-page TOC.

    Args:
        project_root: Absolute project root directory.
        output_dir: Relative output directory (e.g. ``build/html``).
        filesystem: Filesystem service used for writing.

    Returns:
        Script artifact on success, plus any write diagnostics.
    """
    from scribpy.builders.html_single_page_assets import toc_script

    artifact_path = project_root / output_dir / _SCRIPT_OUTPUT_PATH
    try:
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        filesystem.write_text(artifact_path, toc_script())
    except Exception as exc:
        return None, (
            Diagnostic(
                severity="error",
                code="BLD006",
                message=f"Cannot write HTML script artifact: {exc}",
                path=artifact_path,
                hint="Check that the build directory is writable.",
            ),
        )
    return (
        BuildArtifact(
            path=artifact_path, target="html", artifact_type="script"
        ),
        (),
    )


def write_single_page_support_artifacts(
    project_root: Path,
    html: str,
    output_dir: Path,
    filesystem: FileSystem,
) -> tuple[tuple[BuildArtifact, ...], tuple[Diagnostic, ...]]:
    """Write the document and JavaScript assets for single-page HTML.

    Args:
        project_root: Absolute project root directory.
        html: Complete HTML document content.
        output_dir: Relative output directory (e.g. ``build/html``).
        filesystem: Filesystem service used for writing.

    Returns:
        Produced artifacts plus diagnostics.
    """
    artifact, html_diags = write_single_page_artifact(
        project_root, html, output_dir, filesystem
    )
    if artifact is None:
        return (), html_diags

    script_artifact, script_diags = write_single_page_script_artifact(
        project_root, output_dir, filesystem
    )
    if script_artifact is None:
        return (), (*html_diags, *script_diags)
    return (artifact, script_artifact), (*html_diags, *script_diags)


__all__ = [
    "build_single_page_html",
    "render_markdown_to_html",
    "write_single_page_artifact",
    "write_single_page_script_artifact",
    "write_single_page_support_artifacts",
]
