"""Shared local Markdown image collection."""

from __future__ import annotations

import re
import shutil
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

_IMAGE_PATTERN = re.compile(
    r"!\[(?P<alt>[^\]]*)]\((?P<target>[^)\n]*)\)",
)
_EXTERNAL_SCHEMES = frozenset({"http", "https", "ftp", "ftps", "mailto"})


def collect_images(
    content: str,
    source_dir: Path,
    assets_dir: Path,
    reference_prefix: str = "assets",
    collected: dict[str, Path] | None = None,
) -> str:
    """Copy local images and rewrite their Markdown targets.

    Args:
        content: Markdown source text.
        source_dir: Directory used to resolve relative source image targets.
        assets_dir: Directory receiving collected images.
        reference_prefix: POSIX path written before collected filenames.
        collected: Optional export-wide destination-to-source registry.

    Returns:
        Markdown with copied local image targets rewritten.

    Raises:
        OSError: If a local image cannot be copied.
    """
    assets_dir.mkdir(parents=True, exist_ok=True)
    registry = {} if collected is None else collected

    def _replace(match: re.Match[str]) -> str:
        """Copy and replace one local image reference.

        Args:
            match: Markdown image regular-expression match.

        Returns:
            Original or rewritten Markdown image reference.
        """
        raw_target = match.group("target").strip()
        if _is_external(raw_target):
            return match.group(0)
        source_path = _resolve_source(source_dir, raw_target)
        if source_path is None or not source_path.is_file():
            return match.group(0)
        destination_name = _deduplicated_name(source_path, registry)
        registry[destination_name] = source_path
        destination = assets_dir / destination_name
        if not destination.exists():
            shutil.copy2(source_path, destination)
        reference = PurePosixPath(reference_prefix) / destination_name
        return f"![{match.group('alt')}]({reference})"

    return _IMAGE_PATTERN.sub(_replace, content)


def _is_external(target: str) -> bool:
    """Return whether an image target is external.

    Args:
        target: Raw image target.

    Returns:
        True for a URL with an external scheme or network location.
    """
    parsed = urlsplit(target)
    return parsed.scheme in _EXTERNAL_SCHEMES or bool(parsed.netloc)


def _resolve_source(source_dir: Path, target: str) -> Path | None:
    """Resolve one local image target.

    Args:
        source_dir: Directory used to resolve relative targets.
        target: Raw local image target.

    Returns:
        Resolved path, or None for an empty target.
    """
    stripped = target.strip()
    if not stripped:
        return None
    path = Path(stripped)
    if path.is_absolute():
        return source_dir / path.relative_to("/")
    return source_dir / path


def _deduplicated_name(
    source_path: Path,
    collected: dict[str, Path],
) -> str:
    """Return a stable available destination name for an image.

    Args:
        source_path: Source image path.
        collected: Destination-to-source registry for the export.

    Returns:
        Filename that does not collide with another collected source.
    """
    name = source_path.name
    existing = collected.get(name)
    if existing is None or existing == source_path:
        return name
    prefixed = f"{source_path.parent.name}_{name}"
    candidate = prefixed
    suffix = 2
    while candidate in collected and collected[candidate] != source_path:
        candidate = f"{source_path.parent.name}_{suffix}_{name}"
        suffix += 1
    return candidate


__all__ = ["collect_images"]
