"""Build the documentation tutorial project through Scribpy's Python API."""

from pathlib import Path

import scribpy


def main() -> None:
    """Create, validate, assemble, and export the tutorial handbook."""
    root = Path("handbook-api")
    build = Path("build-api")
    scribpy.init_skeleton(
        root,
        title="Team Handbook",
        author="Documentation Team",
        version="1.0.0",
    )
    guide = root / "guide"
    assets = root / "assets"
    guide.mkdir()
    assets.mkdir()

    scribpy.MarkdownFile(
        path=root / "index.md",
        content=(
            "# Welcome\n\n"
            "![Logo](assets/logo.png)\n\n"
            "Read the [installation guide](guide/installation.md).\n"
        ),
    ).write()
    scribpy.MarkdownFile(
        path=guide / "installation.md",
        content=(
            "# Installation\n\n"
            "Install the package in an isolated environment.\n\n"
            "Steps:\n\n"
            "- Create the environment.\n"
            "- Install the package.\n"
        ),
    ).write()

    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d494844520000000100000001"
        "08060000001f15c4890000000d4944415408d763f8cfc0f01f"
        "00050001ff89993d1d0000000049454e44ae426082"
    )
    (assets / "logo.png").write_bytes(png)
    (root / "scribpy.yml").write_text(
        """project:
  title: Team Handbook
  author: Documentation Team
  version: 1.0.0
build:
  toc: true
  toc_depth: 3
  heading_numbering:
    enabled: true
order:
  - index.md
  - guide/
  - assets/
""",
        encoding="utf-8",
    )
    (guide / "scribpy.yml").write_text(
        """title: User guide
order:
  - installation.md
""",
        encoding="utf-8",
    )

    report = scribpy.validate_project(root)
    if not report.is_valid:
        scribpy.render_validation_report(report)
        raise SystemExit(1)

    build.mkdir()
    collection = scribpy.MarkdownCollection.from_tree(root)
    scribpy.concatenate(collection, build / "handbook.md")
    scribpy.html_export(
        build / "handbook.md",
        build / "handbook.html",
    )
    scribpy.mkdocs_export(root, build / "handbook-site")
    print("Created build-api/handbook.md, handbook.html, and handbook-site/")


if __name__ == "__main__":
    main()
