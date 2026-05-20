"""MkDocs site scaffold builder."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path, PurePosixPath

from scribpy.model import BuildArtifact, Diagnostic, TransformedDocument
from scribpy.model.protocols import FileSystem

_MKDOCS_FILENAME = "mkdocs.yml"
_DOCS_DIR = "docs"
_CSS_SUBDIR = "css"
_RENDERED_SITE_DIR = "site"


def build_mkdocs_yaml(
    site_name: str,
    nav_entries: list[dict[str, str]],
    extra_css: list[str],
    theme: str | None = None,
) -> str:
    """Generate ``mkdocs.yml`` content.

    Args:
        site_name: Human-readable site name.
        nav_entries: Ordered nav entries as ``{title: path}`` mappings.
        extra_css: CSS hrefs declared in ``extra_css``.
        theme: Optional MkDocs theme name.

    Returns:
        ``mkdocs.yml`` content as a string.
    """
    lines = [f"site_name: {_yaml_str(site_name)}", ""]
    lines.extend(['site_url: ""', "use_directory_urls: false", ""])

    if theme:
        lines.append(f"theme: {_yaml_str(theme)}")
        lines.append("")

    if extra_css:
        lines.append("extra_css:")
        for href in extra_css:
            lines.append(f"  - {_yaml_str(href)}")
        lines.append("")

    if nav_entries:
        lines.append("nav:")
        for entry in nav_entries:
            for title, path in entry.items():
                lines.append(f"  - {_yaml_str(title)}: {_yaml_str(path)}")
        lines.append("")

    return "\n".join(lines)


def write_site_artifacts(
    project_root: Path,
    documents: tuple[TransformedDocument, ...],
    site_name: str,
    output_dir: Path,
    filesystem: FileSystem,
    theme: str | None = None,
) -> tuple[tuple[BuildArtifact, ...], tuple[Diagnostic, ...]]:
    """Write MkDocs scaffold artifacts to disk.

    Args:
        project_root: Absolute project root directory.
        documents: Transformed documents in build order.
        site_name: Site name for ``mkdocs.yml``.
        output_dir: Relative output directory (e.g. ``build/site``).
        filesystem: Filesystem service used for writing.
        theme: Optional MkDocs theme name.

    Returns:
        Produced artifacts plus diagnostics.
    """
    abs_output = project_root / output_dir
    docs_dir = abs_output / _DOCS_DIR

    page_artifacts, page_diagnostics, nav_entries = _write_pages(
        documents, docs_dir, filesystem
    )
    if page_diagnostics:
        return (), page_diagnostics

    mkdocs_content = build_mkdocs_yaml(
        site_name, nav_entries, extra_css=[], theme=theme
    )
    mkdocs_path = abs_output / _MKDOCS_FILENAME
    try:
        abs_output.mkdir(parents=True, exist_ok=True)
        filesystem.write_text(mkdocs_path, mkdocs_content)
    except Exception as exc:
        return (), (
            Diagnostic(
                severity="error",
                code="SITE001",
                message=f"Cannot write mkdocs.yml: {exc}",
                path=mkdocs_path,
                hint="Check that the build directory is writable.",
            ),
        )

    mkdocs_artifact = BuildArtifact(
        path=mkdocs_path, target="html-site", artifact_type="mkdocs-config"
    )
    return (mkdocs_artifact, *page_artifacts), ()


def write_site_artifacts_with_css(
    project_root: Path,
    documents: tuple[TransformedDocument, ...],
    site_name: str,
    output_dir: Path,
    css_sources: tuple[Path, ...],
    filesystem: FileSystem,
    theme: str | None = None,
) -> tuple[tuple[BuildArtifact, ...], tuple[Diagnostic, ...]]:
    """Write MkDocs scaffold artifacts including CSS files.

    Args:
        project_root: Absolute project root directory.
        documents: Transformed documents in build order.
        site_name: Site name for ``mkdocs.yml``.
        output_dir: Relative output directory (e.g. ``build/site``).
        css_sources: CSS file paths relative to the project root.
        filesystem: Filesystem service used for writing.
        theme: Optional MkDocs theme name.

    Returns:
        Produced artifacts plus diagnostics.
    """
    abs_output = project_root / output_dir
    docs_dir = abs_output / _DOCS_DIR

    page_artifacts, page_diagnostics, nav_entries = _write_pages(
        documents, docs_dir, filesystem
    )
    if page_diagnostics:
        return (), page_diagnostics

    css_artifacts, css_diagnostics, extra_css_hrefs = _copy_css_files(
        project_root, css_sources, docs_dir, filesystem
    )
    if css_diagnostics:
        return (), css_diagnostics

    mkdocs_content = build_mkdocs_yaml(
        site_name, nav_entries, extra_css=extra_css_hrefs, theme=theme
    )
    mkdocs_path = abs_output / _MKDOCS_FILENAME
    try:
        abs_output.mkdir(parents=True, exist_ok=True)
        filesystem.write_text(mkdocs_path, mkdocs_content)
    except Exception as exc:
        return (), (
            Diagnostic(
                severity="error",
                code="SITE001",
                message=f"Cannot write mkdocs.yml: {exc}",
                path=mkdocs_path,
                hint="Check that the build directory is writable.",
            ),
        )

    mkdocs_artifact = BuildArtifact(
        path=mkdocs_path, target="html-site", artifact_type="mkdocs-config"
    )
    return (mkdocs_artifact, *page_artifacts, *css_artifacts), ()


def run_mkdocs_build(
    project_root: Path,
    output_dir: Path,
) -> tuple[BuildArtifact | None, tuple[Diagnostic, ...]]:
    """Render the prepared MkDocs project through the bundled wrapper.

    Args:
        project_root: Absolute Scribpy project root.
        output_dir: Relative directory containing ``mkdocs.yml`` and ``docs/``.

    Returns:
        Final rendered-site artifact plus diagnostics.
    """
    abs_output = project_root / output_dir
    config_path = abs_output / _MKDOCS_FILENAME
    site_dir = abs_output / _RENDERED_SITE_DIR
    command = (
        sys.executable,
        "-m",
        "mkdocs",
        "build",
        "--config-file",
        str(config_path),
        "--site-dir",
        str(site_dir),
    )
    try:
        completed = subprocess.run(
            command,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return None, (_mkdocs_diagnostic("SITE003", f"Cannot execute MkDocs: {exc}"),)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        message = "MkDocs build failed."
        if detail:
            message = f"{message} {detail}"
        return None, (_mkdocs_diagnostic("SITE003", message),)
    return (
        BuildArtifact(path=site_dir, target="html-site", artifact_type="site"),
        (),
    )


def _write_pages(
    documents: tuple[TransformedDocument, ...],
    docs_dir: Path,
    filesystem: FileSystem,
) -> tuple[tuple[BuildArtifact, ...], tuple[Diagnostic, ...], list[dict[str, str]]]:
    """Write pages."""
    artifacts: list[BuildArtifact] = []
    nav_entries: list[dict[str, str]] = []

    for document in documents:
        page_path = docs_dir / document.relative_path
        try:
            page_path.parent.mkdir(parents=True, exist_ok=True)
            filesystem.write_text(page_path, document.content)
        except Exception as exc:
            return (
                (),
                (
                    Diagnostic(
                        severity="error",
                        code="SITE002",
                        message=f"Cannot write site page: {exc}",
                        path=page_path,
                        hint="Check that the docs directory is writable.",
                    ),
                ),
                [],
            )
        artifacts.append(
            BuildArtifact(path=page_path, target="html-site", artifact_type="page")
        )
        nav_title = _page_title(document)
        nav_path = str(PurePosixPath(document.relative_path))
        nav_entries.append({nav_title: nav_path})

    return tuple(artifacts), (), nav_entries


def _copy_css_files(
    project_root: Path,
    css_sources: tuple[Path, ...],
    docs_dir: Path,
    filesystem: FileSystem,
) -> tuple[tuple[BuildArtifact, ...], tuple[Diagnostic, ...], list[str]]:
    """Copy css files."""
    artifacts: list[BuildArtifact] = []
    hrefs: list[str] = []

    css_dir = docs_dir / _CSS_SUBDIR
    for css_source in css_sources:
        abs_source = project_root / css_source
        if not filesystem.exists(abs_source):
            return (
                (),
                (
                    Diagnostic(
                        severity="error",
                        code="CSS001",
                        message=f"CSS file not found: {css_source}",
                        path=abs_source,
                        hint=(
                            "Check that the css_files path is relative to "
                            "the project root."
                        ),
                    ),
                ),
                [],
            )
        dest = css_dir / css_source.name
        try:
            css_dir.mkdir(parents=True, exist_ok=True)
            content = filesystem.read_text(abs_source)
            filesystem.write_text(dest, content)
        except Exception as exc:
            return (
                (),
                (
                    Diagnostic(
                        severity="error",
                        code="CSS002",
                        message=f"Cannot copy CSS file {css_source.name}: {exc}",
                        path=dest,
                        hint="Check that the docs/css directory is writable.",
                    ),
                ),
                [],
            )
        artifacts.append(
            BuildArtifact(path=dest, target="html-site", artifact_type="stylesheet")
        )
        hrefs.append(f"{_CSS_SUBDIR}/{css_source.name}")

    return tuple(artifacts), (), hrefs


def _page_title(document: TransformedDocument) -> str:
    """Return the page title."""
    if document.source_document.title:
        return document.source_document.title
    return document.relative_path.stem.replace("-", " ").replace("_", " ").title()


def _yaml_str(value: str) -> str:
    """Quote a YAML str."""
    if any(c in value for c in (":", "#", "'", '"', "[", "]", "{", "}")):
        escaped = value.replace("'", "''")
        return f"'{escaped}'"
    return value


def _mkdocs_diagnostic(code: str, message: str) -> Diagnostic:
    """Handle mkdocs diagnostic."""
    return Diagnostic(
        severity="error",
        code=code,
        message=message,
        hint="Install MkDocs and ensure the generated project builds successfully.",
    )


__all__ = [
    "build_mkdocs_yaml",
    "run_mkdocs_build",
    "write_site_artifacts",
    "write_site_artifacts_with_css",
]
