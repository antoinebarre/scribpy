"""Small executable example of Scribpy's public Python API."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

# Allow `python main.py` from the repository root without installing the package.
sys.path.insert(0, str(Path(__file__).parent / "src"))

import scribpy


def main() -> None:
    """Show the public API on both a valid and an invalid project."""
    demo_dir = Path("work/api-demo")
    invalid_dir = Path("work/api-invalid-demo")

    # Recreate the demo from scratch so every run starts from the same state.
    if demo_dir.exists():
        shutil.rmtree(demo_dir)
    with scribpy.logging_context(level="INFO", console=True):
        create_result = scribpy.create_demo(demo_dir)
        print("create_demo:", not create_result.failed)

        # These calls mirror the CLI checks:
        # `scribpy index check`, `scribpy parse check`, and `scribpy lint`.
        index_result = scribpy.check_index(demo_dir)
        parse_result = scribpy.check_parse(demo_dir)
        lint_result = scribpy.lint(demo_dir)

        print("check_index:", not index_result.failed)
        print(
            "check_parse:",
            not parse_result.failed,
            f"({len(parse_result.documents)} docs)",
        )
        print("lint:", not lint_result.failed)

        # These calls mirror the CLI builds:
        # `scribpy build markdown` and `scribpy build html`.
        markdown_result = scribpy.build_markdown(demo_dir)
        html_result = scribpy.build_html(demo_dir, mode="single-page")
        site_result = scribpy.build_html(demo_dir, mode="site")

    print("build_markdown:", markdown_result.success)
    print("build_html single-page:", html_result.success)
    print("build_html site:", site_result.success)

    print("\nGenerated artifacts:")
    for result in (markdown_result, html_result, site_result):
        for artifact in result.artifacts:
            print("-", artifact.path)

    # A second demo shows what callers receive when linting fails.
    if invalid_dir.exists():
        shutil.rmtree(invalid_dir)
    scribpy.create_demo(invalid_dir, variant="invalid")
    invalid_lint = scribpy.lint(invalid_dir)

    print("\nInvalid demo lint:", not invalid_lint.failed)
    for diagnostic in invalid_lint.diagnostics:
        print("-", diagnostic.code, diagnostic.message)


if __name__ == "__main__":
    main()
