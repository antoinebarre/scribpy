"""Run a small phase 2 Scribpy project-context demo."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
DEMO_ROOT = ROOT / "demo"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from scribpy.cli.main import main as cli_main  # noqa: E402
from scribpy.config import load_config  # noqa: E402
from scribpy.core import run_index_check  # noqa: E402
from scribpy.model import Diagnostic  # noqa: E402
from scribpy.project import (  # noqa: E402
    build_document_index,
    resolve_project_root,
    scan_project,
)
from scribpy.utils import format_diagnostics  # noqa: E402


def main() -> int:
    """Run the project context and document index demo.

    Returns:
        Process exit code from the CLI check.
    """
    config_path = DEMO_ROOT / "scribpy.toml"
    print(f"Demo project: {DEMO_ROOT.relative_to(ROOT)}")
    print(f"Configuration: {config_path.relative_to(ROOT)}")
    print()

    config, config_diagnostics = load_config(config_path)
    _print_diagnostics("Configuration diagnostics", config_diagnostics)
    if config is None:
        return 1

    project_root = resolve_project_root(config_path)
    source_files, scan_diagnostics = scan_project(project_root, config)
    _print_diagnostics("Scan diagnostics", scan_diagnostics)

    print("Discovered Markdown files:")
    for source_file in source_files:
        print(f"  - {source_file.relative_path.as_posix()}")
    print()

    index, index_diagnostics = build_document_index(config, source_files)
    _print_diagnostics("Index diagnostics", index_diagnostics)

    if index is not None:
        print(f"Document index mode: {index.mode}")
        print("Document index order:")
        for path in index.paths:
            print(f"  - {path.as_posix()}")
        print()

    api_result = run_index_check(DEMO_ROOT)
    print(f"API run_index_check failed: {api_result.failed}")
    _print_diagnostics("API diagnostics", api_result.diagnostics)

    print("CLI command: scribpy index check --root demo")
    cli_exit_code = cli_main(["index", "check", "--root", str(DEMO_ROOT)])
    print(f"CLI exit code: {cli_exit_code}")
    return cli_exit_code


def _print_diagnostics(title: str, diagnostics: tuple[Diagnostic, ...]) -> None:
    print(f"{title}:")
    if not diagnostics:
        print("  none")
        print()
        return

    print(format_diagnostics(diagnostics))
    print()


if __name__ == "__main__":
    raise SystemExit(main())
