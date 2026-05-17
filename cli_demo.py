"""Run the public CLI end-to-end on disposable demo projects under ``work/``."""

from __future__ import annotations

import shutil
import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

# Allow `python cli_demo.py` from the repository root without installing the package.
sys.path.insert(0, str(Path(__file__).parent / "src"))

from scribpy.cli.main import main as cli_main


def main() -> int:
    """Exercise the main CLI workflows on generated demo projects.

    Returns:
        Process exit code. ``0`` means every expected CLI scenario behaved as
        intended; ``1`` means at least one command returned an unexpected code.
    """
    valid_dir = Path("work/cli-demo")
    invalid_dir = Path("work/cli-invalid-demo")

    _reset(valid_dir)
    _reset(invalid_dir)

    expected_results = (
        _run(
            "Create valid demo",
            ["demo", "create", str(valid_dir)],
            expected=0,
        ),
        _run(
            "Check index",
            ["index", "check", "--root", str(valid_dir)],
            expected=0,
        ),
        _run(
            "Check parse",
            ["parse", "check", "--root", str(valid_dir)],
            expected=0,
        ),
        _run(
            "Lint valid project",
            ["lint", "--root", str(valid_dir)],
            expected=0,
        ),
        _run(
            "Build Markdown",
            ["build", "markdown", "--root", str(valid_dir)],
            expected=0,
        ),
        _run(
            "Build single-page HTML",
            ["build", "html", "--mode", "single-page", "--root", str(valid_dir)],
            expected=0,
        ),
        _run(
            "Build site HTML",
            ["build", "html", "--mode", "site", "--root", str(valid_dir)],
            expected=0,
        ),
        _run(
            "Create invalid demo",
            ["demo", "create", str(invalid_dir), "--variant", "invalid"],
            expected=0,
        ),
        _run(
            "Lint invalid project",
            ["lint", "--root", str(invalid_dir)],
            expected=1,
        ),
    )

    print("CLI demo summary")
    print("────────────────")
    failed = False
    for result in expected_results:
        mark = "✔" if result.matched else "✘"
        print(
            f"{mark} {result.label}: expected {result.expected}, "
            f"received {result.actual}"
        )
        failed = failed or not result.matched
    return 1 if failed else 0


def _reset(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def _run(label: str, argv: list[str], *, expected: int) -> CommandResult:
    print()
    print(label)
    print("─" * len(label))
    print(f"$ scribpy {' '.join(argv)}")
    actual, stdout, stderr = _capture_cli(argv)
    if stdout:
        print(stdout, end="" if stdout.endswith("\n") else "\n")
    if stderr:
        print(stderr, end="" if stderr.endswith("\n") else "\n")
    return CommandResult(
        label=label,
        expected=expected,
        actual=actual,
    )


def _capture_cli(argv: list[str]) -> tuple[int, str, str]:
    stdout = StringIO()
    stderr = StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        actual = cli_main(argv)
    return actual, stdout.getvalue(), stderr.getvalue()


class CommandResult:
    """Outcome of one CLI demo command.

    Attributes:
        label: Human-readable scenario name.
        expected: Exit code expected from the scenario.
        actual: Exit code returned by the CLI.
    """

    def __init__(self, label: str, expected: int, actual: int) -> None:
        self.label = label
        self.expected = expected
        self.actual = actual

    @property
    def matched(self) -> bool:
        """Return whether the actual exit code matched the expectation.

        Returns:
            Whether the scenario behaved as expected.
        """
        return self.actual == self.expected


if __name__ == "__main__":
    raise SystemExit(main())
