"""Generate the code metrics compliance report."""

from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from quality_config import load_quality_config
from report_common import base_metadata

from scribpy.report import (
    BlockQuote,
    Chapter,
    Paragraph,
    Report,
    Section,
    Table,
    Text,
)

WORK = Path("work")
_NAMESPACE = load_quality_config().config_namespace
OUT_PATH = WORK / "reports" / "report_metrics.md"
FILE_METRICS_JSON = WORK / "metrics_by_file.json"


def _per_file_chapter(json_path: Path) -> Chapter | None:
    """Build a per-file metrics table chapter from the JSON data.

    Args:
        json_path: Path to the ``metrics_by_file.json`` file.

    Returns:
        A ``Chapter`` node or ``None`` if the file is missing or empty.
    """
    if not json_path.exists():
        return None
    try:
        data: list[dict[str, object]] = json.loads(
            json_path.read_text(encoding="utf-8")
        )
    except (json.JSONDecodeError, OSError):
        return None
    if not data:
        return None

    rows = [
        [
            str(entry["path"]),
            str(entry["max_cc"]),
            f"{float(entry['avg_cc']):.2f}",
            f"{float(entry['mi']):.1f}",
            str(entry["sloc"]),
            str(entry["lloc"]),
            f"{float(entry['docstring_pct']):.1f}%",
        ]
        for entry in data
    ]
    return (
        Chapter(title="Metrics by File")
        .add(
            Paragraph(
                [
                    Text(f"{len(data)} source files analysed. "),
                    Text(
                        "CC max = highest cyclomatic complexity in the file, "
                        "MI = maintainability index (0–100, higher is better), "
                        "SLOC = source lines of code, LLOC = logical lines."
                    ),
                ]
            )
        )
        .add(
            Table(
                headers=[
                    "File",
                    "CC max",
                    "CC avg",
                    "MI",
                    "SLOC",
                    "LLOC",
                    "Docstring %",
                ],
                rows=rows,
            )
        )
    )


def main() -> None:
    """Build the code metrics report from the existing metrics log and config."""
    config = _load_config(Path("pyproject.toml"))
    log_body = _read_log(WORK / "metrics.log")
    rows, passed_count, failed_count = _parse_metrics_log(log_body)

    report = (
        Report(
            title="Code Metrics",
            metadata=base_metadata("Code Metrics", "metrics"),
        )
        .add(
            Chapter(title="Summary")
            .add(
                Paragraph(
                    [
                        Text(f"{passed_count}", style="bold"),
                        Text(" metrics passed, "),
                        Text(f"{failed_count}", style="bold"),
                        Text(" failed."),
                    ]
                )
            )
            .add(
                Table(
                    headers=["Metric", "Threshold", "Actual", "Status"],
                    rows=rows,
                )
            )
        )
        .add(_thresholds_chapter(config))
    )

    per_file = _per_file_chapter(FILE_METRICS_JSON)
    if per_file is not None:
        report.add(per_file)

    if failed_count:
        report.add(
            Chapter(title="Failures").add(
                BlockQuote(
                    "\n".join(
                        f"{r[0]}: expected {r[1]}, got {r[2]}"
                        for r in rows
                        if r[3] == "❌ FAIL"
                    )
                )
            )
        )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report.save(str(OUT_PATH))
    print(f"Written: {OUT_PATH}")


def _read_log(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _parse_metrics_log(body: str) -> tuple[list[list[str]], int, int]:
    """Extract metric rows from the plain-text metrics log.

    Returns:
        Tuple of (rows, passed_count, failed_count).
    """
    rows: list[list[str]] = []
    passed = 0
    failed = 0
    for line in body.splitlines():
        parts = [p.strip() for p in line.split("  ") if p.strip()]
        if len(parts) >= 4 and parts[-1] in ("PASSED", "FAILED"):
            status = parts[-1]
            name = parts[0]
            expected = parts[1] if len(parts) > 1 else ""
            actual = parts[2] if len(parts) > 2 else ""
            icon = "✅ pass" if status == "PASSED" else "❌ FAIL"
            rows.append([name, expected, actual, icon])
            if status == "PASSED":
                passed += 1
            else:
                failed += 1
    return rows, passed, failed


def _load_config(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    with path.open("rb") as f:
        data = tomllib.load(f)
    return data.get("tool", {}).get(_NAMESPACE, {}).get("code_metrics", {})


def _thresholds_chapter(config: dict[str, object]) -> Chapter:
    fields = [
        ("max_cyclomatic_complexity", "Max cyclomatic complexity"),
        ("max_average_complexity", "Average cyclomatic complexity"),
        ("min_maintainability_index", "Min maintainability index"),
        ("max_module_logical_lines", "Max logical lines per module"),
        ("max_module_source_lines", "Max source lines per module"),
    ]
    rows = [[label, str(config.get(key, "n/a"))] for key, label in fields]
    return Chapter(title="Configured Thresholds").add(
        Section(title="Active Configuration")
        .add(
            Paragraph(
                [
                    Text("Thresholds are loaded from "),
                    Text("pyproject.toml", style="code"),
                    Text(" section "),
                    Text(f"[tool.{_NAMESPACE}.code_metrics]", style="code"),
                    Text("."),
                ]
            )
        )
        .add(Table(headers=["Metric", "Threshold"], rows=rows))
    )


if __name__ == "__main__":
    main()
