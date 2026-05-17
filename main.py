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

    _section("Valid project workflow")
    with scribpy.logging_context(level="INFO", console=False):
        create_result = scribpy.create_demo(demo_dir)
        _step("Create demo project", not create_result.failed)

        # These calls mirror the CLI checks:
        # `scribpy index check`, `scribpy parse check`, and `scribpy lint`.
        index_result = scribpy.check_index(demo_dir)
        parse_result = scribpy.check_parse(demo_dir)
        lint_result = scribpy.lint(demo_dir)

        _step("Validate document index", not index_result.failed)
        _step("Parse project documents", not parse_result.failed)
        _step("Run lint rules", not lint_result.failed)
        print(f"  Parsed documents: {len(parse_result.documents)}")

        # These calls mirror the CLI builds:
        # `scribpy build markdown` and `scribpy build html`.
        markdown_result = scribpy.build_markdown(demo_dir)
        html_result = scribpy.build_html(demo_dir, mode="single-page")
        site_result = scribpy.build_html(demo_dir, mode="site")

    _step("Build Markdown", markdown_result.success)
    _step("Build HTML single-page", html_result.success)
    _step("Build HTML site", site_result.success)
    _artifact_summary("Markdown", markdown_result)
    _artifact_summary("HTML single-page", html_result)
    _artifact_summary("HTML site", site_result)

    # A second demo shows what callers receive when linting fails.
    if invalid_dir.exists():
        shutil.rmtree(invalid_dir)
    scribpy.create_demo(invalid_dir, variant="invalid")
    invalid_lint = scribpy.lint(invalid_dir)

    _section("Invalid project diagnostics")
    _step("Run lint rules", not invalid_lint.failed)
    scribpy.print_result(invalid_lint)


def _section(title: str) -> None:
    print(title)
    print("─" * len(title))


def _step(label: str, succeeded: bool) -> None:
    mark = "✔" if succeeded else "✘"
    status = "done" if succeeded else "failed"
    print(f"{mark} {label} — {status}")


def _artifact_summary(label: str, result: scribpy.BuildResult) -> None:
    if not result.success or not result.artifacts:
        return
    primary = result.artifacts[0]
    for artifact_type in ("document", "site", "page"):
        match = next(
            (
                artifact
                for artifact in result.artifacts
                if artifact.artifact_type == artifact_type
            ),
            None,
        )
        if match is not None:
            primary = match
            break
    print(f"  {label}: {primary.path}")
    if len(result.artifacts) > 1:
        print(f"    additional artifacts: {len(result.artifacts) - 1}")


if __name__ == "__main__":
    main()
