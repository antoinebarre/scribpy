"""Demonstrate Scribpy core Markdown features.

The demo writes input and output examples under ``work/demo`` so the current
core behavior can be inspected without reading the tests.
"""

from __future__ import annotations

import shutil
import sys
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scribpy import MarkdownCollection, MarkdownDocument, MarkdownFile

DEMO_ROOT = Path("work/demo")
INPUT_ROOT = DEMO_ROOT / "input"
OUTPUT_ROOT = DEMO_ROOT / "output"
REPOSITORY_ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = REPOSITORY_ROOT / "src"


def main() -> None:
    """Create demo inputs, run Scribpy core features, and write outputs."""
    _add_source_root_to_path()
    markdown_collection, markdown_file = _scribpy_classes()

    _reset_demo_tree()
    _create_demo_inputs()

    collection = markdown_collection.from_tree(INPUT_ROOT)
    document = collection.concatenate()
    single_file = markdown_file.from_path(INPUT_ROOT / "02-images.md")
    updated_file = single_file.replace_text("Images", "Image inventory")

    _write_output("assembled.md", document.content)
    _write_output("summary.md", _summary(collection, document, single_file))
    _write_output("single-file-updated.md", updated_file.content)

    _announce_demo_paths()


def _reset_demo_tree() -> None:
    """Reset the demo directory before writing fresh examples."""
    if DEMO_ROOT.exists():
        shutil.rmtree(DEMO_ROOT)
    INPUT_ROOT.mkdir(parents=True)
    OUTPUT_ROOT.mkdir(parents=True)


def _create_demo_inputs() -> None:
    """Write Markdown input examples and future scribpy.yml manifests."""
    _write_input(
        "scribpy.yml",
        "project:\n"
        "  title: Scribpy core demo\n"
        "build:\n"
        "  toc: true\n"
        "  renumber_headings: false\n"
        "order:\n"
        "  - 01-intro.md\n"
        "  - 02-images.md\n"
        "  - guide/\n"
        "  - assets/\n",
    )
    _write_input(
        "01-intro.md",
        "# Intro\n\n"
        "This file opens the assembled document.\n\n"
        "[Next chapter](guide/01-install.md)\n",
    )
    _write_input(
        "02-images.md",
        "# Images\n\n"
        "A local image reference is captured as metadata.\n\n"
        '![Logo](assets/logo.svg "Demo logo")\n',
    )
    _write_input(
        "guide/scribpy.yml",
        "title: Guide\norder:\n  - 01-install.md\n  - 02-run.markdown\n",
    )
    _write_input(
        "guide/01-install.md",
        "# Install\n\nInstall instructions can live in a nested folder.\n",
    )
    _write_input(
        "guide/02-run.markdown",
        "# Run\n\nThe collection also accepts `.markdown` files.\n",
    )
    _write_input(
        "notes.txt",
        "This file is intentionally ignored by MarkdownCollection.\n",
    )
    _write_input(
        "assets/logo.svg",
        '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32">'
        '<rect width="32" height="32" fill="#2f6fed"/>'
        "</svg>\n",
    )


def _summary(
    collection: MarkdownCollection,
    document: MarkdownDocument,
    single_file: MarkdownFile,
) -> str:
    """Return a Markdown summary of the demo results.

    Args:
        collection: Loaded Markdown collection.
        document: Concatenated Markdown document.
        single_file: Markdown file used to demonstrate file-level validation.

    Returns:
        Markdown summary text.
    """
    lines = [
        "# Scribpy Core Demo",
        "",
        "## Discovered Markdown files",
        "",
    ]
    lines.extend(
        f"- `{markdown_file.path.relative_to(INPUT_ROOT).as_posix()}`"
        for markdown_file in collection.files
    )
    lines.extend(
        [
            "",
            "## Concatenated document",
            "",
            f"- Project title: `{collection.manifest.project.get('title')}`",
            f"- TOC setting: `{collection.manifest.build.get('toc')}`",
            f"- Character count: `{len(document.content)}`",
            f"- Image references: `{len(document.image_references)}`",
            "",
            "## Image references",
            "",
        ],
    )
    lines.extend(_image_reference_lines(document))
    lines.extend(
        [
            "",
            "## File-level checks",
            "",
            f"- `02-images.md` has valid images: "
            f"`{single_file.has_valid_images()}`",
            f"- `02-images.md` has expected heading: "
            f"`{single_file.has_expected_headings(((1, 'Images'),))}`",
            "",
            "## Notes",
            "",
            "- The root `scribpy.yml` contains project metadata, build "
            "settings, and first-level order.",
            "- Folder `scribpy.yml` files contain local title and order only.",
        ],
    )
    return "\n".join(lines) + "\n"


def _image_reference_lines(document: MarkdownDocument) -> list[str]:
    """Return summary lines for image references.

    Args:
        document: Markdown document containing image references.

    Returns:
        Markdown bullet lines describing the document image references.
    """
    if not document.image_references:
        return ["- No image references found."]
    return [
        "- "
        f"line `{reference.line}`, column `{reference.column}`: "
        f"`{reference.alt_text}` -> `{reference.target}`"
        for reference in document.image_references
    ]


def _announce_demo_paths() -> None:
    """Write generated demo paths to standard output."""
    sys.stdout.write(f"Demo generated in {DEMO_ROOT}\n")
    sys.stdout.write(f"Inputs:  {INPUT_ROOT}\n")
    sys.stdout.write(f"Outputs: {OUTPUT_ROOT}\n")


def _add_source_root_to_path() -> None:
    """Add the local ``src`` directory to Python imports for repo demos."""
    source_root = str(SOURCE_ROOT)
    if source_root not in sys.path:
        sys.path.insert(0, source_root)


def _scribpy_classes() -> tuple[type[MarkdownCollection], type[MarkdownFile]]:
    """Load Scribpy classes after the local source path is configured.

    Returns:
        Markdown collection and file classes from the local source tree.
    """
    scribpy = import_module("scribpy")
    return scribpy.MarkdownCollection, scribpy.MarkdownFile


def _write_input(relative_path: str, content: str) -> None:
    """Write one demo input file.

    Args:
        relative_path: File path relative to the demo input root.
        content: UTF-8 file content.
    """
    path = INPUT_ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_output(relative_path: str, content: str) -> None:
    """Write one demo output file.

    Args:
        relative_path: File path relative to the demo output root.
        content: UTF-8 file content.
    """
    path = OUTPUT_ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
