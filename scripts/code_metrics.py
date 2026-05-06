"""Check code metrics configured in pyproject.toml."""

from __future__ import annotations

import fnmatch
import tomllib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from radon.complexity import cc_visit
from radon.metrics import mi_visit
from radon.raw import analyze


@dataclass(frozen=True)
class MetricsConfig:
    """Thresholds used by the code metrics compliance check."""

    paths: tuple[Path, ...]
    exclude: tuple[str, ...]
    max_cyclomatic_complexity: int
    max_average_complexity: float
    min_maintainability_index: float
    max_module_logical_lines: int
    max_module_source_lines: int
    report_path: Path


@dataclass(frozen=True)
class MetricResult:
    """A single code metric comparison."""

    name: str
    expected: str
    actual: str
    passed: bool


def main() -> int:
    """Run the configured metrics checks."""
    config = _load_config(Path("pyproject.toml"))
    files = tuple(_iter_python_files(config))
    total_complexity = 0
    total_blocks = 0
    max_complexity = 0
    max_complexity_label = "no analyzed block"
    min_maintainability_index = 100.0
    min_maintainability_label = "no analyzed file"
    max_logical_lines = 0
    max_logical_lines_label = "no analyzed file"
    max_source_lines = 0
    max_source_lines_label = "no analyzed file"

    for file_path in files:
        source = file_path.read_text(encoding="utf-8")
        blocks = cc_visit(source)
        raw_metrics = analyze(source)
        maintainability_index = mi_visit(source, True)

        for block in blocks:
            total_complexity += block.complexity
            total_blocks += 1
            if block.complexity > max_complexity:
                max_complexity = block.complexity
                max_complexity_label = f"{file_path}:{block.lineno} {block.name}"

        if maintainability_index < min_maintainability_index:
            min_maintainability_index = maintainability_index
            min_maintainability_label = file_path.as_posix()

        if raw_metrics.lloc > max_logical_lines:
            max_logical_lines = raw_metrics.lloc
            max_logical_lines_label = file_path.as_posix()

        if raw_metrics.sloc > max_source_lines:
            max_source_lines = raw_metrics.sloc
            max_source_lines_label = file_path.as_posix()

    average_complexity = total_complexity / total_blocks if total_blocks else 0.0
    results = (
        MetricResult(
            name="Max cyclomatic complexity",
            expected=f"<= {config.max_cyclomatic_complexity}",
            actual=f"{max_complexity} ({max_complexity_label})",
            passed=max_complexity <= config.max_cyclomatic_complexity,
        ),
        MetricResult(
            name="Average cyclomatic complexity",
            expected=f"<= {config.max_average_complexity:.2f}",
            actual=f"{average_complexity:.2f}",
            passed=average_complexity <= config.max_average_complexity,
        ),
        MetricResult(
            name="Minimum maintainability index",
            expected=f">= {config.min_maintainability_index:.2f}",
            actual=f"{min_maintainability_index:.2f} ({min_maintainability_label})",
            passed=min_maintainability_index >= config.min_maintainability_index,
        ),
        MetricResult(
            name="Max module logical lines",
            expected=f"<= {config.max_module_logical_lines}",
            actual=f"{max_logical_lines} ({max_logical_lines_label})",
            passed=max_logical_lines <= config.max_module_logical_lines,
        ),
        MetricResult(
            name="Max module source lines",
            expected=f"<= {config.max_module_source_lines}",
            actual=f"{max_source_lines} ({max_source_lines_label})",
            passed=max_source_lines <= config.max_module_source_lines,
        ),
    )
    _write_report(config.report_path, files, total_blocks, results)
    failures = tuple(result for result in results if not result.passed)

    if failures:
        print("Code metrics check failed:")
        _print_results(results)
        for failure in failures:
            print(
                f"- {failure.name}: expected {failure.expected}, "
                f"actual {failure.actual}"
            )
        print(f"Code metrics report written to {config.report_path}")
        return 1

    print(
        "Code metrics passed: "
        f"{len(files)} files, {total_blocks} blocks, "
        f"average complexity {average_complexity:.2f}"
    )
    _print_results(results)
    print(f"Code metrics report written to {config.report_path}")
    return 0


def _load_config(path: Path) -> MetricsConfig:
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    table = raw["tool"]["scribpy"]["code_metrics"]

    return MetricsConfig(
        paths=tuple(Path(value) for value in _tuple(table["paths"])),
        exclude=_tuple(table.get("exclude", ())),
        max_cyclomatic_complexity=int(table["max_cyclomatic_complexity"]),
        max_average_complexity=float(table["max_average_complexity"]),
        min_maintainability_index=float(table["min_maintainability_index"]),
        max_module_logical_lines=int(table["max_module_logical_lines"]),
        max_module_source_lines=int(table["max_module_source_lines"]),
        report_path=Path(str(table["report_path"])),
    )


def _iter_python_files(config: MetricsConfig) -> tuple[Path, ...]:
    files: list[Path] = []
    for path in config.paths:
        if path.is_file() and path.suffix == ".py":
            candidates = (path,)
        else:
            candidates = tuple(path.rglob("*.py"))
        files.extend(
            candidate
            for candidate in candidates
            if not _is_excluded(candidate, config.exclude)
        )
    return tuple(sorted(files))


def _is_excluded(path: Path, patterns: tuple[str, ...]) -> bool:
    normalized = path.as_posix()
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in patterns)


def _tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, list | tuple):
        return tuple(str(item) for item in value)
    raise TypeError("Expected a TOML array of strings")


def _write_report(
    path: Path,
    files: tuple[Path, ...],
    total_blocks: int,
    results: tuple[MetricResult, ...],
) -> None:
    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    passed = sum(result.passed for result in results)
    failed = len(results) - passed
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Code Metrics Report",
        "",
        f"Generated at: `{generated_at}`",
        "",
        f"Scope: **{len(files)} files**, **{total_blocks} blocks**.",
        "",
        f"Summary: **{passed} passed**, **{failed} failed**.",
        "",
        "| Metric | Expected | Actual | Status |",
        "|--------|----------|--------|--------|",
    ]
    for result in results:
        status = "PASSED" if result.passed else "FAILED"
        lines.append(
            "| "
            f"{result.name} | "
            f"{_escape_table(result.expected)} | "
            f"{_escape_table(result.actual)} | "
            f"{status} |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _print_results(results: tuple[MetricResult, ...]) -> None:
    name_width = max(len("Metric"), *(len(result.name) for result in results))
    expected_width = max(len("Expected"), *(len(result.expected) for result in results))
    print("")
    print(
        f"{'Metric':<{name_width}}  "
        f"{'Expected':<{expected_width}}  "
        f"{'Actual'}  "
        f"{'Status'}"
    )
    print(f"{'-' * name_width}  {'-' * expected_width}  {'-' * 48}  {'-' * 6}")
    for result in results:
        status = "PASSED" if result.passed else "FAILED"
        print(
            f"{result.name:<{name_width}}  "
            f"{result.expected:<{expected_width}}  "
            f"{result.actual:<48}  "
            f"{status}"
        )
    print("")


def _escape_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


if __name__ == "__main__":
    raise SystemExit(main())
