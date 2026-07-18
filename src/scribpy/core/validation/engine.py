"""Project validation orchestration."""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from pathlib import Path

import mkforge

from scribpy.core.diagnostics import DiagnosticSeverity
from scribpy.core.manifest import (
    MANIFEST_NAME,
    FolderManifest,
    RootManifest,
    load_folder_manifest,
    load_root_manifest,
)
from scribpy.core.markdown_collection import MarkdownCollection
from scribpy.core.markdown_patterns import _MARKDOWN_SUFFIXES
from scribpy.core.validation.model import (
    ProjectDiagnostic,
    ProjectValidationReport,
)
from scribpy.errors import InvalidScribpyManifestError, ScribpyManifestWarning


@dataclass(frozen=True, slots=True)
class _ManifestInspection:
    """Hold manifest validation findings and inspected count.

    Attributes:
        diagnostics: Findings emitted while reading manifests.
        count: Number of manifest files inspected.
    """

    diagnostics: tuple[ProjectDiagnostic, ...]
    count: int


def validate_project(root: str | Path) -> ProjectValidationReport:
    """Validate the structure and Markdown content of a Scribpy project.

    Args:
        root: Project directory containing Markdown and manifests.

    Returns:
        Structured validation report without console output.
    """
    project_root = Path(root)
    if not project_root.is_dir():
        return ProjectValidationReport(
            root=project_root,
            diagnostics=(
                ProjectDiagnostic(
                    code="PROJECT_ROOT_NOT_DIRECTORY",
                    severity=DiagnosticSeverity.ERROR,
                    message="Project root is not an existing directory.",
                    path=project_root,
                ),
            ),
        )
    inspection = _inspect_manifests(project_root)
    if _has_errors(inspection.diagnostics):
        return ProjectValidationReport(
            root=project_root,
            diagnostics=inspection.diagnostics,
            manifest_count=inspection.count,
        )
    collection, loading_diagnostics = _load_collection(project_root)
    if collection is None:
        return ProjectValidationReport(
            root=project_root,
            diagnostics=inspection.diagnostics + loading_diagnostics,
            manifest_count=inspection.count,
        )
    diagnostics = (
        inspection.diagnostics
        + loading_diagnostics
        + _verify_markdown(collection)
        + _adapt_collection_diagnostics(collection)
    )
    return ProjectValidationReport(
        root=project_root,
        diagnostics=diagnostics,
        markdown_count=len(collection.files),
        manifest_count=inspection.count,
    )


def _inspect_manifests(root: Path) -> _ManifestInspection:
    """Inspect every manifest reachable below the project root.

    Args:
        root: Existing project directory.

    Returns:
        Manifest findings and number of inspected manifest files.
    """
    paths = tuple(sorted(root.rglob(MANIFEST_NAME)))
    diagnostics = tuple(
        diagnostic
        for path in paths
        for diagnostic in _inspect_manifest(root, path)
    )
    return _ManifestInspection(diagnostics=diagnostics, count=len(paths))


def _inspect_manifest(
    root: Path,
    path: Path,
) -> tuple[ProjectDiagnostic, ...]:
    """Inspect one root or folder manifest.

    Args:
        root: Project root used to identify the root manifest.
        path: Manifest file to inspect.

    Returns:
        Diagnostics emitted for the manifest.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ScribpyManifestWarning)
        try:
            manifest = _load_manifest(root, path)
        except (InvalidScribpyManifestError, OSError, UnicodeError) as exc:
            return (_manifest_error(path, exc),)
    return _order_diagnostics(path, manifest.order)


def _load_manifest(root: Path, path: Path) -> RootManifest | FolderManifest:
    """Load the manifest matching its position in the project.

    Args:
        root: Project root directory.
        path: Manifest path.

    Returns:
        Parsed root or folder manifest.

    Raises:
        InvalidScribpyManifestError: If the manifest is invalid.
        OSError: If the manifest cannot be read.
        UnicodeError: If the manifest cannot be decoded.
    """
    if path == root / MANIFEST_NAME:
        return load_root_manifest(root)
    return load_folder_manifest(path.parent)


def _manifest_error(path: Path, error: Exception) -> ProjectDiagnostic:
    """Convert a manifest loading exception into a project diagnostic.

    Args:
        path: Manifest that could not be loaded.
        error: Expected loading failure.

    Returns:
        Blocking manifest diagnostic.
    """
    detail = getattr(error, "detail", str(error))
    return ProjectDiagnostic(
        code="MANIFEST_INVALID",
        severity=DiagnosticSeverity.ERROR,
        message=str(detail),
        path=path,
        category="manifest",
    )


def _order_diagnostics(
    path: Path,
    order: tuple[str, ...],
) -> tuple[ProjectDiagnostic, ...]:
    """Validate ordered child declarations from one manifest.

    Args:
        path: Manifest declaring the child names.
        order: Normalized ordered child names.

    Returns:
        Missing, unsupported, and duplicate entry diagnostics.
    """
    diagnostics: list[ProjectDiagnostic] = []
    seen: set[str] = set()
    for entry in order:
        if entry in seen:
            diagnostics.append(_order_error(path, entry, "is duplicated"))
        seen.add(entry)
        child = path.parent / entry
        if not child.exists():
            diagnostics.append(_order_error(path, entry, "does not exist"))
        elif not _is_supported_order_target(child):
            diagnostics.append(
                _order_error(path, entry, "is not Markdown or a directory")
            )
    return tuple(diagnostics)


def _order_error(path: Path, entry: str, detail: str) -> ProjectDiagnostic:
    """Build one blocking order-entry diagnostic.

    Args:
        path: Manifest containing the entry.
        entry: Declared child name.
        detail: Explanation of the violation.

    Returns:
        Blocking manifest diagnostic.
    """
    return ProjectDiagnostic(
        code="MANIFEST_ORDER_INVALID",
        severity=DiagnosticSeverity.ERROR,
        message=f"Ordered child {entry!r} {detail}.",
        path=path,
        category="manifest",
        target=entry,
    )


def _is_supported_order_target(path: Path) -> bool:
    """Return whether an ordered child can belong to a collection.

    Args:
        path: Existing ordered child.

    Returns:
        True for directories and supported Markdown files.
    """
    return path.is_dir() or (
        path.is_file() and path.suffix.lower() in _MARKDOWN_SUFFIXES
    )


def _load_collection(
    root: Path,
) -> tuple[MarkdownCollection | None, tuple[ProjectDiagnostic, ...]]:
    """Load the collection and capture expected project warnings.

    Args:
        root: Existing project root.

    Returns:
        Loaded collection when successful and loading diagnostics.
    """
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ScribpyManifestWarning)
        try:
            collection = MarkdownCollection.from_tree(root)
        except (InvalidScribpyManifestError, OSError, UnicodeError) as exc:
            diagnostic = ProjectDiagnostic(
                code="PROJECT_LOAD_FAILED",
                severity=DiagnosticSeverity.ERROR,
                message=str(exc),
                path=root,
            )
            return None, (diagnostic,)
    diagnostics = tuple(
        ProjectDiagnostic(
            code="MANIFEST_WARNING",
            severity=DiagnosticSeverity.WARNING,
            message=str(item.message),
            category="manifest",
        )
        for item in caught
        if issubclass(item.category, ScribpyManifestWarning)
    )
    return collection, diagnostics


def _verify_markdown(
    collection: MarkdownCollection,
) -> tuple[ProjectDiagnostic, ...]:
    """Verify every collection file with Mkforge.

    Args:
        collection: Loaded project collection.

    Returns:
        Adapted Mkforge diagnostics.
    """
    return tuple(
        _adapt_mkforge_diagnostic(markdown_file.path, diagnostic)
        for markdown_file in collection.files
        for diagnostic in markdown_file.verify().diagnostics
    )


def _adapt_mkforge_diagnostic(
    path: Path,
    diagnostic: mkforge.Diagnostic,
) -> ProjectDiagnostic:
    """Adapt one Mkforge conformance diagnostic for project reporting.

    Args:
        path: Markdown file verified by Mkforge.
        diagnostic: Mkforge finding to adapt.

    Returns:
        Blocking project diagnostic preserving Mkforge metadata.
    """
    return ProjectDiagnostic(
        code=diagnostic.rule_id,
        severity=DiagnosticSeverity.ERROR,
        message=diagnostic.message,
        path=path,
        line=diagnostic.line,
        column=diagnostic.column,
        category=diagnostic.category,
        target=diagnostic.target,
    )


def _adapt_collection_diagnostics(
    collection: MarkdownCollection,
) -> tuple[ProjectDiagnostic, ...]:
    """Adapt project-aware collection diagnostics.

    Args:
        collection: Loaded project collection.

    Returns:
        Project diagnostics preserving collection severity.
    """
    return tuple(
        ProjectDiagnostic(
            code=item.code,
            severity=item.severity,
            message=item.message,
            path=item.path,
            line=item.line,
            category="collection",
        )
        for item in collection.diagnose().diagnostics
    )


def _has_errors(diagnostics: tuple[ProjectDiagnostic, ...]) -> bool:
    """Return whether diagnostics contain a blocking finding.

    Args:
        diagnostics: Project findings to inspect.

    Returns:
        True when at least one finding has error severity.
    """
    return any(
        item.severity == DiagnosticSeverity.ERROR for item in diagnostics
    )
