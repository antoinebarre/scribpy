"""Asset collection and copy helpers."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from scribpy.model import BuildArtifact, Diagnostic, Document, TransformedDocument
from scribpy.model.protocols import FileSystem


def collect_asset_paths(
    documents: tuple[Document, ...],
    source_root: Path,
) -> tuple[Path, ...]:
    """Collect unique absolute asset paths referenced across all documents.

    Args:
        documents: Parsed source documents.
        source_root: Absolute root from which relative asset paths are
            resolved.

    Returns:
        Unique absolute asset paths in deterministic order.
    """
    seen: set[Path] = set()
    ordered: list[Path] = []
    for document in documents:
        for asset in document.assets:
            if asset.path is not None:
                candidate = asset.path
            else:
                if _is_external(asset.target):
                    continue
                candidate = Path(asset.target)
            if _is_external(str(candidate)):
                continue
            abs_path = (document.path.parent / candidate).resolve()
            if abs_path not in seen:
                seen.add(abs_path)
                ordered.append(abs_path)
    return tuple(ordered)


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
            diagnostics.append(
                Diagnostic(
                    severity="warning",
                    code="ASS001",
                    message=f"Asset not found, skipping copy: {abs_path}",
                    path=abs_path,
                    hint=("Ensure the asset file exists at the referenced path."),
                )
            )
            continue
        try:
            rel = abs_path.relative_to(source_root)
        except ValueError:
            rel = Path(abs_path.name)
        dest = dest_dir / rel
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            content = filesystem.read_text(abs_path)
            filesystem.write_text(dest, content)
        except Exception as exc:
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="ASS002",
                    message=f"Cannot copy asset {abs_path.name}: {exc}",
                    path=dest,
                    hint="Check that the asset destination is writable.",
                )
            )
            continue
        artifacts.append(
            BuildArtifact(path=dest, target="assets", artifact_type="image")
        )

    return tuple(artifacts), tuple(diagnostics)


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
                        hint="Check that the css directory is writable.",
                    ),
                ),
                [],
            )
        artifacts.append(
            BuildArtifact(path=dest, target="html", artifact_type="stylesheet")
        )
        hrefs.append(f"css/{css_source.name}")

    return tuple(artifacts), (), hrefs


def rewrite_asset_links_single_page(
    documents: tuple[TransformedDocument, ...],
    source_root: Path,
) -> tuple[TransformedDocument, ...]:
    """Rewrite local image links for the flattened single-page output.

    Single-page HTML is written beside one shared ``assets/`` directory, while
    source Markdown image links are relative to each source document. This
    function rewrites only local image targets and leaves remote URLs intact.

    Args:
        documents: Target-ready documents that will be flattened into one page.
        source_root: Absolute source directory used to preserve asset subpaths.

    Returns:
        Documents whose local image links point into the shared asset directory.
    """
    rewritten: list[TransformedDocument] = []
    for document in documents:
        content = document.content
        for asset in document.source_document.assets:
            if asset.path is None or _is_external(asset.target):
                continue
            abs_path = (document.source_document.path.parent / asset.path).resolve()
            try:
                rel = abs_path.relative_to(source_root)
            except ValueError:
                rel = Path(abs_path.name)
            content = content.replace(
                f"]({asset.target})",
                f"](assets/{rel.as_posix()})",
            )
        rewritten.append(replace(document, content=content))
    return tuple(rewritten)


def _is_external(path: str) -> bool:
    return path.startswith(("http://", "https://", "//", "mailto:"))


__all__ = [
    "collect_asset_paths",
    "copy_assets",
    "copy_css_files_single_page",
    "rewrite_asset_links_single_page",
]
