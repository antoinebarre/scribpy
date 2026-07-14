"""scribpy.yml manifest loading and validation."""

from __future__ import annotations

import warnings
from pathlib import Path, PurePosixPath
from typing import Annotated, Any

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from scribpy.errors import InvalidScribpyManifestError, ScribpyManifestWarning

MANIFEST_NAME = "scribpy.yml"
_ROOT_KEYS = frozenset({"project", "build", "order"})
_FOLDER_KEYS = frozenset({"title", "order"})


class HeadingNumberingSettings(BaseModel):
    """Represent the build.heading_numbering sub-mapping.

    Attributes:
        enabled: Whether MkForge heading numbering is applied.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: Annotated[bool, Field(strict=True)] = True


class BuildSettings(BaseModel):
    """Represent the build section of a root scribpy.yml manifest.

    Attributes:
        toc: Whether to insert a table of contents after the first H1.
        toc_depth: Maximum heading depth included in the TOC.
        heading_numbering: Heading numbering configuration block.
        renumber_headings: Legacy alias for heading_numbering.enabled.
        plantuml_backend: Backend name for PlantUML rendering.
        mermaid_backend: Backend name for Mermaid rendering.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    toc: Annotated[bool, Field(strict=True)] = False
    toc_depth: Annotated[int, Field(ge=1, strict=True)] = 3
    heading_numbering: HeadingNumberingSettings | None = None
    renumber_headings: Annotated[bool, Field(strict=True)] | None = None
    plantuml_backend: str = "web"
    mermaid_backend: str = "web"

    @field_validator("toc_depth", mode="before")
    @classmethod
    def _reject_bool_as_depth(cls, value: object) -> object:
        """Reject boolean values for toc_depth.

        Args:
            value: Raw field value.

        Returns:
            Unchanged value when it is not a boolean.

        Raises:
            ValueError: If value is a boolean.
        """
        if isinstance(value, bool):
            msg = "'build.toc_depth' must be a positive integer"
            raise ValueError(msg)
        return value


class RootManifest(BaseModel):
    """Represent the root scribpy.yml project manifest.

    Attributes:
        path: Root manifest path, when present.
        project: Project metadata values.
        build: Global build settings.
        order: Optional ordered direct children of the root folder.
    """

    model_config = ConfigDict(frozen=True)

    path: Path | None = None
    project: dict[str, object] = Field(default_factory=dict)
    build: BuildSettings = Field(default_factory=BuildSettings)
    order: tuple[str, ...] = ()


class FolderManifest(BaseModel):
    """Represent a folder-level scribpy.yml manifest.

    Attributes:
        path: Folder manifest path, when present.
        title: Optional replacement title for the folder.
        order: Optional ordered direct children of the folder.
    """

    model_config = ConfigDict(frozen=True)

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
    _warn_unknown_keys(path, data, _ROOT_KEYS)
    return RootManifest(
        path=path,
        project=_pop_optional_mapping(path, data, "project"),
        build=_parse_build_settings(path, data),
        order=_pop_optional_order(path, data),
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
    _warn_unknown_keys(path, data, _FOLDER_KEYS)
    return FolderManifest(
        path=path,
        title=_pop_optional_title(path, data),
        order=_pop_optional_order(path, data),
    )


def heading_numbering_enabled(manifest: RootManifest) -> bool:
    """Return whether heading numbering is enabled for a root manifest.

    Args:
        manifest: Root manifest containing build settings.

    Returns:
        True when MkForge heading numbering should be applied.
    """
    if manifest.build.heading_numbering is not None:
        return manifest.build.heading_numbering.enabled
    if manifest.build.renumber_headings is not None:
        return manifest.build.renumber_headings
    return False


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
    """Read a YAML manifest as a string-keyed mapping.

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
            str(path), "manifest must be a mapping"
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
            stacklevel=3,
        )


def _pop_optional_mapping(
    path: Path,
    data: dict[str, object],
    key: str,
) -> dict[str, object]:
    """Extract and return an optional nested mapping from manifest data.

    Args:
        path: Manifest file path.
        data: Parsed manifest data.
        key: Manifest key to read.

    Returns:
        Mapping value or an empty mapping.

    Raises:
        InvalidScribpyManifestError: If the value is not a mapping.
    """
    value = data.pop(key, {})
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise InvalidScribpyManifestError(
            str(path), f"{key!r} must be a mapping"
        )
    return _string_key_mapping(path, value)


def _parse_build_settings(
    path: Path,
    data: dict[str, object],
) -> BuildSettings:
    """Extract and parse the build section into a BuildSettings model.

    Args:
        path: Manifest file path.
        data: Parsed manifest data (build key is consumed).

    Returns:
        Validated BuildSettings instance.

    Raises:
        InvalidScribpyManifestError: If the build section is malformed.
    """
    raw = _pop_optional_mapping(path, data, "build")
    _warn_heading_numbering_override(path, raw)
    try:
        return BuildSettings.model_validate(raw)
    except Exception as exc:
        raise InvalidScribpyManifestError(str(path), str(exc)) from exc


def _warn_heading_numbering_override(
    path: Path,
    build: dict[str, object],
) -> None:
    """Warn when the legacy alias is shadowed by the canonical setting.

    Args:
        path: Manifest file path.
        build: Parsed build mapping.
    """
    if "heading_numbering" in build and "renumber_headings" in build:
        warnings.warn(
            f"Ignoring 'renumber_headings' in {path}; "
            "'heading_numbering' takes precedence",
            ScribpyManifestWarning,
            stacklevel=4,
        )


def _pop_optional_title(path: Path, data: dict[str, object]) -> str | None:
    """Extract and return an optional folder title.

    Args:
        path: Manifest file path.
        data: Parsed manifest data.

    Returns:
        Folder title or None.

    Raises:
        InvalidScribpyManifestError: If the title is not a string.
    """
    value = data.pop("title", None)
    if value is None:
        return None
    if not isinstance(value, str):
        raise InvalidScribpyManifestError(
            str(path), "'title' must be a string"
        )
    return value


def _pop_optional_order(
    path: Path, data: dict[str, object]
) -> tuple[str, ...]:
    """Extract and return optional manifest order entries.

    Args:
        path: Manifest file path.
        data: Parsed manifest data.

    Returns:
        Ordered entry names, or an empty tuple.

    Raises:
        InvalidScribpyManifestError: If order is not a string list.
    """
    value = data.pop("order", None)
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
