"""Image collection for assembled Markdown documents."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from urllib.parse import urlsplit

_IMAGE_PATTERN = re.compile(
    r"!\[(?P<alt>[^\]]*)]\((?P<target>[^)\n]*)\)",
)
_EXTERNAL_SCHEMES = frozenset({"http", "https", "ftp", "ftps", "mailto"})


def collect_images(
    content: str,
    source_root: Path,
    assets_dir: Path,
) -> str:
    """Copy local images to the assets directory and rewrite their paths.

    Each local image reference in *content* is rewritten to point to the
    copied file inside *assets_dir*.  External images (HTTP/HTTPS/…) are
    left unchanged.  When two source images share the same filename, the
    second one is prefixed with its parent folder name to avoid collision.

    Args:
        content: Markdown source text of the assembled document.
        source_root: Collection root directory used to resolve relative paths.
        assets_dir: Destination directory for collected image files.

    Returns:
        Markdown source text with local image paths rewritten.
    """
    assets_dir.mkdir(parents=True, exist_ok=True)
    collected: dict[str, Path] = {}

    def _replace(match: re.Match[str]) -> str:
        raw_target = match.group("target").strip()
        alt = match.group("alt")
        if _is_external(raw_target):
            return match.group(0)
        source_path = _resolve_source(source_root, raw_target)
        if source_path is None or not source_path.is_file():
            return match.group(0)
        dest_name = _deduplicated_name(source_path, collected)
        collected[dest_name] = source_path
        dest = assets_dir / dest_name
        if not dest.exists():
            shutil.copy2(source_path, dest)
        return f"![{alt}](assets/{dest_name})"

    return _IMAGE_PATTERN.sub(_replace, content)


def _is_external(target: str) -> bool:
    """Return whether an image target is an external URL.

    Args:
        target: Raw image target string.

    Returns:
        True when the target uses an external URL scheme.
    """
    parsed = urlsplit(target)
    return parsed.scheme in _EXTERNAL_SCHEMES or bool(parsed.netloc)


def _resolve_source(root: Path, target: str) -> Path | None:
    """Resolve a local image target to an absolute path.

    Args:
        root: Collection root directory.
        target: Raw local image target.

    Returns:
        Resolved absolute path, or None when the target is empty.
    """
    stripped = target.strip()
    if not stripped:
        return None
    path = Path(stripped)
    if path.is_absolute():
        return root / path.relative_to("/")
    return root / path


def _deduplicated_name(
    source_path: Path,
    collected: dict[str, Path],
) -> str:
    """Return a unique filename for an image in the assets directory.

    When the bare filename is already taken by a different source path, the
    parent folder name is prepended as a prefix.

    Args:
        source_path: Absolute source image path.
        collected: Already-collected filename-to-source mapping.

    Returns:
        Deduplicated filename for use in the assets directory.
    """
    name = source_path.name
    existing = collected.get(name)
    if existing is None or existing == source_path:
        return name
    prefix = source_path.parent.name
    return f"{prefix}_{name}"
