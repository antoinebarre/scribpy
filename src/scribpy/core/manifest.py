"""scribpy.yml manifest loading and validation."""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from scribpy.errors import InvalidScribpyManifestError, ScribpyManifestWarning

MANIFEST_NAME = "scribpy.yml"
ROOT_KEYS = frozenset({"project", "build", "order"})
FOLDER_KEYS = frozenset({"title", "order"})


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
    return RootManifest(
        path=path,
        project=_optional_mapping(path, data, "project"),
        build=_optional_mapping(path, data, "build"),
        order=_optional_order(path, data),
    )


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
