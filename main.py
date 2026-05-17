"""Run the public Scribpy Python API end to end from the repository root."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import scribpy

_WORK_DIR = Path(__file__).parent / "work"
_DEMO_DIR = _WORK_DIR / "api-demo"


def _section(title: str) -> None:
    print(f"\n{'─' * 64}")
    print(f"  {title}")
    print(f"{'─' * 64}")


def _print_diagnostics(diagnostics: tuple[object, ...]) -> None:
    if not diagnostics:
        print("  diagnostics: none")
        return
    print("  diagnostics:")
    for diagnostic in diagnostics:
        print(f"    - {diagnostic.severity} {diagnostic.code}: {diagnostic.message}")


def _prepare_demo_project() -> None:
    _section("create_demo")
    if _DEMO_DIR.exists():
        shutil.rmtree(_DEMO_DIR)
    result = scribpy.create_demo(_DEMO_DIR)
    print(f"  created: {_DEMO_DIR.relative_to(Path(__file__).parent)}")
    print(f"  failed: {result.failed}")
    _print_diagnostics(result.diagnostics)


def _run_checks() -> None:
    _section("check_index")
    index_result = scribpy.check_index(_DEMO_DIR)
    print(f"  failed: {index_result.failed}")
    _print_diagnostics(index_result.diagnostics)

    _section("check_parse")
    parse_result = scribpy.check_parse(_DEMO_DIR)
    print(f"  failed: {parse_result.failed}")
    print(f"  documents: {len(parse_result.documents)}")
    _print_diagnostics(parse_result.diagnostics)

    _section("lint")
    lint_result = scribpy.lint(_DEMO_DIR)
    print(f"  failed: {lint_result.failed}")
    _print_diagnostics(lint_result.diagnostics)


def _print_build_result(name: str, result: scribpy.BuildResult) -> None:
    _section(name)
    print(f"  success: {result.success}")
    _print_diagnostics(result.diagnostics)
    print("  artifacts:")
    for artifact in result.artifacts:
        try:
            display_path = artifact.path.relative_to(_DEMO_DIR)
        except ValueError:
            display_path = artifact.path
        print(f"    - {artifact.target}/{artifact.artifact_type}: {display_path}")


def _run_builds() -> None:
    _print_build_result("build_markdown", scribpy.build_markdown(_DEMO_DIR))
    _print_build_result(
        "build_html(mode='single-page')",
        scribpy.build_html(_DEMO_DIR, mode="single-page"),
    )
    _print_build_result(
        "build_html(mode='site')",
        scribpy.build_html(_DEMO_DIR, mode="site"),
    )


def main() -> None:
    """Run the full public-API demo."""
    print("scribpy — public Python API demo")
    print("using only `import scribpy` from this script")

    _WORK_DIR.mkdir(exist_ok=True)
    _prepare_demo_project()
    _run_checks()
    _run_builds()

    print("\nDone.")
    print(f"Inspect generated files under: {_DEMO_DIR}")


if __name__ == "__main__":
    main()
