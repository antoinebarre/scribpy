"""scribpy.yml manifest loading and validation."""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, cast

import yaml

from scribpy.errors import InvalidScribpyManifestError, ScribpyManifestWarning

MANIFEST_NAME = "scribpy.yml"
ROOT_KEYS = frozenset({"project", "build", "order"})
FOLDER_KEYS = frozenset({"title", "order"})
HEADING_NUMBERING_KEYS = frozenset({"enabled"})


@dataclass(frozen=True, slots=True)
class RootManifest:
    """Represent the root scribpy.yml project manifest.

    Attributes:
        path: Root manifest path, when present.
        project: Project metadata values.
        build: Global build settings.
        order: Optional ordered direct children of the root folder.
    """

    path: Path | None = None
    project: dict[str, object] = field(default_factory=dict)
    build: dict[str, object] = field(default_factory=dict)
    order: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class FolderManifest:
    """Represent a folder-level scribpy.yml manifest.

    Attributes:
        path: Folder manifest path, when present.
        title: Optional replacement title for the folder.
        order: Optional ordered direct children of the folder.
    """

    path: Path | None = None
    title: str | None = None
    order: tuple[str, ...] = ()


def load_root_manifest(root: Path) -> RootManifest:
    """Load the root manifest for a collection tree.

    Args:
        root: Collection root directory.

    Returns:
        Root manifest values, or defaults when no manifest exists.

    Raises:
        InvalidScribpyManifestError: If the manifest shape is invalid.
    """
    path = root / MANIFEST_NAME
    if not path.exists():
        return RootManifest()
    data = _read_manifest_mapping(path)
    _warn_unknown_keys(path, data, ROOT_KEYS)
    build = _optional_mapping(path, data, "build")
    _validate_build_settings(path, build)
    return RootManifest(
        path=path,
        project=_optional_mapping(path, data, "project"),
        build=build,
        order=_optional_order(path, data),
    )


def heading_numbering_enabled(manifest: RootManifest) -> bool:
    """Return whether heading numbering is enabled for a root manifest.

    Args:
        manifest: Root manifest containing build settings.

    Returns:
        True when MkForge heading numbering should be applied.
    """
    if "heading_numbering" in manifest.build:
        value = cast("dict[str, object]", manifest.build["heading_numbering"])
        enabled = value.get("enabled", True)
        return enabled is True
    return manifest.build.get("renumber_headings") is True


def load_folder_manifest(folder: Path) -> FolderManifest:
    """Load a folder manifest for a collection subtree.

    Args:
        folder: Folder where a local manifest may exist.

    Returns:
        Folder manifest values, or defaults when no manifest exists.

    Raises:
        InvalidScribpyManifestError: If the manifest shape is invalid.
    """
    path = folder / MANIFEST_NAME
    if not path.exists():
        return FolderManifest()
    data = _read_manifest_mapping(path)
    _warn_unknown_keys(path, data, FOLDER_KEYS)
    return FolderManifest(
        path=path,
        title=_optional_title(path, data),
        order=_optional_order(path, data),
    )


def validate_direct_child_entry(path: Path, entry: str) -> str:
    """Validate and normalize one manifest order entry.

    Args:
        path: Manifest file path.
        entry: Raw order entry.

    Returns:
        Normalized direct child name.

    Raises:
        InvalidScribpyManifestError: If the entry is not a direct child name.
    """
    normalized = entry.strip().rstrip("/")
    parts = PurePosixPath(normalized).parts
    if len(parts) != 1 or normalized in {"", ".", ".."}:
        raise InvalidScribpyManifestError(
            str(path),
            f"order entry must name a direct child: {entry!r}",
        )
    return normalized


def _read_manifest_mapping(path: Path) -> dict[str, object]:
    """Read a YAML manifest as a mapping.

    Args:
        path: Manifest file path.

    Returns:
        Manifest mapping.

    Raises:
        InvalidScribpyManifestError: If YAML cannot be parsed as a mapping.
    """
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise InvalidScribpyManifestError(str(path), str(exc)) from exc
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise InvalidScribpyManifestError(
            str(path),
            "manifest must be a mapping",
        )
    return _string_key_mapping(path, loaded)


def _string_key_mapping(path: Path, data: dict[Any, Any]) -> dict[str, object]:
    """Return a manifest mapping with string keys.

    Args:
        path: Manifest file path.
        data: Parsed YAML mapping.

    Returns:
        Mapping with string keys and object values.

    Raises:
        InvalidScribpyManifestError: If one key is not a string.
    """
    result: dict[str, object] = {}
    for key, value in data.items():
        if not isinstance(key, str):
            raise InvalidScribpyManifestError(
                str(path),
                f"manifest key must be a string: {key!r}",
            )
        result[key] = value
    return result


def _warn_unknown_keys(
    path: Path,
    data: dict[str, object],
    allowed: frozenset[str],
) -> None:
    """Warn about ignored manifest keys.

    Args:
        path: Manifest file path.
        data: Parsed manifest data.
        allowed: Manifest keys accepted at this level.
    """
    for key in sorted(set(data) - allowed):
        warnings.warn(
            f"Ignoring unsupported key {key!r} in {path}",
            ScribpyManifestWarning,
            stacklevel=2,
        )


def _optional_mapping(
    path: Path,
    data: dict[str, object],
    key: str,
) -> dict[str, object]:
    """Return an optional manifest mapping.

    Args:
        path: Manifest file path.
        data: Parsed manifest data.
        key: Manifest key to read.

    Returns:
        Mapping value or an empty mapping.

    Raises:
        InvalidScribpyManifestError: If the value is not a mapping.
    """
    value = data.get(key, {})
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise InvalidScribpyManifestError(
            str(path),
            f"{key!r} must be a mapping",
        )
    return _string_key_mapping(path, value)


def _validate_build_settings(
    path: Path,
    build: dict[str, object],
) -> None:
    """Validate supported build settings with strict nested contracts.

    Args:
        path: Manifest file path.
        build: Parsed build mapping.

    Raises:
        InvalidScribpyManifestError: If a supported setting is malformed.
    """
    _validate_heading_numbering(path, build)
    _validate_legacy_renumber_headings(path, build)
    _warn_ignored_legacy_renumber_headings(path, build)
    _validate_toc(path, build)
    _validate_toc_depth(path, build)


def _validate_toc(
    path: Path,
    build: dict[str, object],
) -> None:
    """Validate the build.toc boolean flag.

    Args:
        path: Manifest file path.
        build: Parsed build mapping.

    Raises:
        InvalidScribpyManifestError: If build.toc is not a boolean.
    """
    if "toc" not in build:
        return
    if not isinstance(build["toc"], bool):
        raise InvalidScribpyManifestError(
            str(path),
            "'build.toc' must be a boolean",
        )


def _validate_toc_depth(
    path: Path,
    build: dict[str, object],
) -> None:
    """Validate the build.toc_depth integer setting.

    Args:
        path: Manifest file path.
        build: Parsed build mapping.

    Raises:
        InvalidScribpyManifestError: If build.toc_depth is not a positive
            integer.
    """
    if "toc_depth" not in build:
        return
    value = build["toc_depth"]
    if not isinstance(value, int) or isinstance(value, bool):
        raise InvalidScribpyManifestError(
            str(path),
            "'build.toc_depth' must be a positive integer",
        )
    if value < 1:
        raise InvalidScribpyManifestError(
            str(path),
            "'build.toc_depth' must be a positive integer",
        )


def _validate_heading_numbering(
    path: Path,
    build: dict[str, object],
) -> None:
    """Validate the build.heading_numbering mapping contract.

    Args:
        path: Manifest file path.
        build: Parsed build mapping.

    Raises:
        InvalidScribpyManifestError: If heading_numbering is malformed.
    """
    if "heading_numbering" not in build:
        return
    value = build["heading_numbering"]
    if not isinstance(value, dict):
        raise InvalidScribpyManifestError(
            str(path),
            "'build.heading_numbering' must be a mapping",
        )
    heading_numbering = _string_key_mapping(path, value)
    unsupported = sorted(set(heading_numbering) - HEADING_NUMBERING_KEYS)
    if unsupported:
        raise InvalidScribpyManifestError(
            str(path),
            (
                "'build.heading_numbering' contains unsupported key: "
                f"{unsupported[0]!r}"
            ),
        )
    enabled = heading_numbering.get("enabled", True)
    if not isinstance(enabled, bool):
        raise InvalidScribpyManifestError(
            str(path),
            "'build.heading_numbering.enabled' must be a boolean",
        )
    build["heading_numbering"] = heading_numbering


def _validate_legacy_renumber_headings(
    path: Path,
    build: dict[str, object],
) -> None:
    """Validate the legacy build.renumber_headings alias.

    Args:
        path: Manifest file path.
        build: Parsed build mapping.

    Raises:
        InvalidScribpyManifestError: If renumber_headings is malformed.
    """
    if "renumber_headings" not in build:
        return
    if not isinstance(build["renumber_headings"], bool):
        raise InvalidScribpyManifestError(
            str(path),
            "'build.renumber_headings' must be a boolean",
        )


def _warn_ignored_legacy_renumber_headings(
    path: Path,
    build: dict[str, object],
) -> None:
    """Warn when the legacy alias is ignored by the canonical setting.

    Args:
        path: Manifest file path.
        build: Parsed build mapping.
    """
    if "heading_numbering" not in build or "renumber_headings" not in build:
        return
    warnings.warn(
        f"Ignoring 'renumber_headings' in {path}; "
        "'heading_numbering' takes precedence",
        ScribpyManifestWarning,
        stacklevel=2,
    )


def _optional_title(path: Path, data: dict[str, object]) -> str | None:
    """Return an optional folder title.

    Args:
        path: Manifest file path.
        data: Parsed manifest data.

    Returns:
        Folder title or None.

    Raises:
        InvalidScribpyManifestError: If the title is not a string.
    """
    value = data.get("title")
    if value is None:
        return None
    if not isinstance(value, str):
        raise InvalidScribpyManifestError(
            str(path),
            "'title' must be a string",
        )
    return value


def _optional_order(path: Path, data: dict[str, object]) -> tuple[str, ...]:
    """Return optional manifest order entries.

    Args:
        path: Manifest file path.
        data: Parsed manifest data.

    Returns:
        Ordered entry names, or an empty tuple.

    Raises:
        InvalidScribpyManifestError: If order is not a string list.
    """
    if "order" not in data:
        return ()
    value = data["order"]
    if value is None:
        return ()
    if not isinstance(value, list):
        raise InvalidScribpyManifestError(str(path), "'order' must be a list")
    return tuple(_order_entry(path, entry) for entry in value)


def _order_entry(path: Path, entry: object) -> str:
    """Return one validated order entry.

    Args:
        path: Manifest file path.
        entry: Raw order entry.

    Returns:
        Normalized order entry.

    Raises:
        InvalidScribpyManifestError: If entry is not a string.
    """
    if not isinstance(entry, str):
        raise InvalidScribpyManifestError(
            str(path),
            f"order entry must be a string: {entry!r}",
        )
    return validate_direct_child_entry(path, entry)
