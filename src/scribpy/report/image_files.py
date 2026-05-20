"""Copy user-supplied report image files into report assets."""

from __future__ import annotations

import shutil
from pathlib import Path


def copy_image_file(source_path: str, assets_dir: Path) -> str:
    """Copy a user-supplied image into the report assets directory.

    The file is copied to ``assets_dir / <filename>``. If a file with the same
    name already exists it is overwritten.

    Args:
        source_path: Path to the original image file.
        assets_dir: Destination directory created when needed.

    Returns:
        A POSIX-style relative path string suitable for GFM embedding.

    Raises:
        FileNotFoundError: If ``source_path`` does not exist.
    """
    src = Path(source_path)
    if not src.exists():
        raise FileNotFoundError(f"ImageFile source not found: {source_path}")
    assets_dir.mkdir(parents=True, exist_ok=True)
    dest = assets_dir / src.name
    shutil.copy2(src, dest)
    return (Path("assets") / src.name).as_posix()


__all__ = ["copy_image_file"]
