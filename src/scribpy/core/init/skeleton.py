"""Minimal scribpy project skeleton initialisation."""

from __future__ import annotations

from pathlib import Path

import yaml

from scribpy.core.manifest import MANIFEST_NAME
from scribpy.errors import ScaffoldCollisionError


def init_skeleton(
    output_dir: Path,
    *,
    title: str,
    author: str = "",
    version: str = "0.1.0",
) -> None:
    """Initialise a minimal scribpy project skeleton in *output_dir*.

    Creates the root ``scribpy.yml`` manifest and a stub ``index.md`` file.
    The output directory is created if it does not already exist. If a
    ``scribpy.yml`` already exists inside *output_dir*, the call is refused to
    prevent overwriting an existing project.

    Args:
        output_dir: Target directory for the new project skeleton.
        title: Project title, written as the H1 of ``index.md`` and into
            the manifest ``project.title`` field.
        author: Optional project author, written into ``project.author``.
        version: Optional project version string, written into
            ``project.version``.

    Raises:
        ScaffoldCollisionError: If *output_dir* already contains a
            ``scribpy.yml`` file.
    """
    manifest_path = output_dir / MANIFEST_NAME
    if manifest_path.exists():
        raise ScaffoldCollisionError(str(manifest_path))

    output_dir.mkdir(parents=True, exist_ok=True)

    _write_root_manifest(
        manifest_path, title=title, author=author, version=version
    )
    _write_index_md(output_dir / "index.md", title=title)


def _write_root_manifest(
    path: Path,
    *,
    title: str,
    author: str,
    version: str,
) -> None:
    """Write the root ``scribpy.yml`` manifest file.

    Args:
        path: Absolute path of the manifest file to create.
        title: Project title.
        author: Project author (omitted from manifest when empty).
        version: Project version string.
    """
    project: dict[str, str] = {"title": title, "version": version}
    if author:
        project["author"] = author

    data: dict[str, object] = {
        "project": project,
        "build": {
            "toc": False,
            "heading_numbering": {"enabled": False},
        },
        "order": ["index.md"],
    }
    path.write_text(
        yaml.dump(data, default_flow_style=False, allow_unicode=True),
        encoding="utf-8",
    )


def _write_index_md(path: Path, *, title: str) -> None:
    """Write a stub ``index.md`` with the project title as H1.

    Args:
        path: Absolute path of the Markdown file to create.
        title: Project title used as the H1 heading.
    """
    path.write_text(f"# {title}\n", encoding="utf-8")
