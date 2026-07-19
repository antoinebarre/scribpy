"""Scaffold generation from a validated outline tree."""

from __future__ import annotations

from pathlib import Path

import yaml
from mkforge.slugify import slugify_heading

from scribpy.core.init.outline_node import OutlineNode
from scribpy.core.init.outline_parser import parse_outline
from scribpy.core.manifest import MANIFEST_NAME
from scribpy.errors import ScaffoldCollisionError


def init_from_outline(
    outline_path: Path,
    output_dir: Path,
    *,
    max_depth: int = 4,
) -> None:
    """Scaffold a scribpy project directory tree from an outline Markdown file.

    Parses *outline_path*, validates its heading structure, then generates an
    arborescence of directories and ``scribpy.yml`` manifests mirroring the
    heading hierarchy. Each heading at depth ≤ *max_depth* becomes either a
    ``.md`` stub file (leaf node) or a subdirectory containing its own
    ``scribpy.yml`` and stubs for its children.

    The root ``scribpy.yml`` is created in *output_dir* with the H1 title as
    ``project.title`` and the list of direct children as ``order``.

    Args:
        outline_path: Path to the outline Markdown file (headings only).
        output_dir: Target root directory for the generated project.
        max_depth: Maximum heading level to scaffold (default 4). Headings
            deeper than this level are rejected during parsing.

    Raises:
        ScaffoldCollisionError: If *output_dir* already contains a
            ``scribpy.yml`` file.
        OutlineValidationError: If *outline_path* is structurally invalid.
        ValueError: If *max_depth* is not between 1 and 6 inclusive.
    """
    manifest_path = output_dir / MANIFEST_NAME
    if manifest_path.exists():
        raise ScaffoldCollisionError(str(manifest_path))

    roots = parse_outline(outline_path, max_depth=max_depth)
    output_dir.mkdir(parents=True, exist_ok=True)
    _scaffold_root(output_dir, roots)


def _scaffold_root(root_dir: Path, roots: list[OutlineNode]) -> None:
    """Write the root manifest and scaffold all top-level nodes.

    When there is exactly one H1 root, its title is used as ``project.title``
    and its children become the direct root-level entries. When there are
    multiple H1 roots, a generic title is used and each H1 becomes a
    top-level entry.

    Args:
        root_dir: Directory where the root manifest is written.
        roots: Top-level H1 OutlineNode objects from the parsed outline.
    """
    if len(roots) == 1:
        project_title = roots[0].title
        children = roots[0].children
    else:
        project_title = "Project"
        children = roots

    order_entries, _ = _scaffold_children(root_dir, children)

    # When there is a single H1 with no sub-headings, keep index.md in order.
    if not order_entries:
        order_entries = ["index.md"]

    _write_root_manifest(
        root_dir / MANIFEST_NAME,
        title=project_title,
        order=order_entries,
    )

    index_path = root_dir / "index.md"
    if not index_path.exists():
        index_path.write_text(f"# {project_title}\n", encoding="utf-8")


def _scaffold_children(
    parent_dir: Path,
    nodes: list[OutlineNode],
) -> tuple[list[str], list[str]]:
    """Scaffold nodes as files or subdirectories inside *parent_dir*.

    A node with no children becomes a ``.md`` stub file. A node with children
    becomes a subdirectory with its own ``scribpy.yml``.

    Args:
        parent_dir: Directory where files and subdirectories are created.
        nodes: Sibling OutlineNode objects to scaffold.

    Returns:
        A pair ``(order_entries, stub_files)`` where *order_entries* is the
        manifest-ready list of direct children names (file names or directory
        names) and *stub_files* lists only the ``.md`` stubs created.
    """
    order_entries: list[str] = []
    stub_files: list[str] = []

    for node in nodes:
        slug = slugify_heading(node.title)
        if node.children:
            subdir = parent_dir / slug
            subdir.mkdir(parents=True, exist_ok=True)
            child_order, _ = _scaffold_children(subdir, node.children)
            _write_folder_manifest(
                subdir / MANIFEST_NAME, node.title, child_order
            )
            order_entries.append(slug)
        else:
            filename = f"{slug}.md"
            stub_path = parent_dir / filename
            stub_path.write_text(f"# {node.title}\n", encoding="utf-8")
            order_entries.append(filename)
            stub_files.append(filename)

    return order_entries, stub_files


def _write_root_manifest(
    path: Path,
    *,
    title: str,
    order: list[str],
) -> None:
    """Write a root ``scribpy.yml`` manifest.

    Args:
        path: Absolute path of the manifest file to create.
        title: Project title written into ``project.title``.
        order: Ordered list of direct child entries.
    """
    data: dict[str, object] = {
        "project": {"title": title},
        "build": {
            "toc": False,
            "heading_numbering": {"enabled": False},
        },
        "order": order,
    }
    path.write_text(
        yaml.dump(data, default_flow_style=False, allow_unicode=True),
        encoding="utf-8",
    )


def _write_folder_manifest(
    path: Path,
    title: str,
    order: list[str],
) -> None:
    """Write a folder ``scribpy.yml`` manifest.

    Args:
        path: Absolute path of the manifest file to create.
        title: Folder title.
        order: Ordered list of direct child entries within the folder.
    """
    data: dict[str, object] = {
        "title": title,
        "order": order,
    }
    path.write_text(
        yaml.dump(data, default_flow_style=False, allow_unicode=True),
        encoding="utf-8",
    )
