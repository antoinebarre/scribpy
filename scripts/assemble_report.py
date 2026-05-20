"""Assemble reports into quality_report.md, zip artefacts, then clean up."""

from __future__ import annotations

import shutil
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from quality_config import load_quality_config

from scribpy.report import MergeSection, merge_markdown

_QC = load_quality_config()

WORK = Path("work")
REPORTS_DIR = WORK / "reports"
# Final report lives directly in work/, not in work/reports/
OUT_PATH = WORK / "quality_report.md"
ZIP_PATH = WORK / "quality_artefacts.zip"

# Individual report files in assembly order; heading_offset=1 demotes H1→H2
PARTS: list[tuple[str, int]] = [
    ("report_files.md", 1),
    ("report_lint.md", 1),
    ("report_metrics.md", 1),
    ("report_tests.md", 1),
]

# Native artefacts with real value beyond what the markdown reports contain:
# XML data (parsed by CI), coverage HTML (interactive), junit (CI test panel).
# Plain .log files are intentionally excluded — they duplicate the reports.
NATIVE_ARTEFACTS: list[str] = [
    "work/junit.xml",
    "work/coverage.xml",
    "work/code-metrics-report.md",
]


def main() -> None:
    """Merge all reports, zip artefacts, clean temp files."""
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    sections, stats = _collect_sections(now)
    merged = merge_markdown(*sections, separator="\n\n---\n\n")
    OUT_PATH.write_text(merged, encoding="utf-8")
    print(f"Written: {OUT_PATH}")

    _zip_artefacts()
    print(f"Written: {ZIP_PATH}")

    _cleanup()


def _collect_sections(
    now: str,
) -> tuple[list[MergeSection], dict[str, object]]:
    """Build all merge sections and collect global stats for the header.

    Args:
        now: Current timestamp string.

    Returns:
        Tuple of (sections list, stats dict).
    """
    stats: dict[str, object] = {"now": now, "missing": [], "parts": []}
    missing: list[str] = stats["missing"]  # type: ignore[assignment]
    part_info: list[dict[str, object]] = stats["parts"]  # type: ignore[assignment]

    for filename, _ in PARTS:
        path = REPORTS_DIR / filename
        if not path.exists():
            missing.append(filename)
            part_info.append({"filename": filename, "found": False})
        else:
            content = path.read_text(encoding="utf-8")
            total, passed, failed = _count_statuses(content)
            part_info.append(
                {
                    "filename": filename,
                    "found": True,
                    "total": total,
                    "passed": passed,
                    "failed": failed,
                }
            )

    header = _make_header(now, part_info, missing)
    sections: list[MergeSection] = [
        MergeSection(content=header, heading_offset=0)
    ]
    for filename, offset in PARTS:
        path = REPORTS_DIR / filename
        if path.exists():
            sections.append(
                MergeSection(
                    content=path.read_text(encoding="utf-8"),
                    heading_offset=offset,
                )
            )
    return sections, stats


def _count_statuses(content: str) -> tuple[int, int, int]:
    """Count ✅/❌ occurrences in a sub-report.

    Args:
        content: Markdown report text.

    Returns:
        Tuple of (total, passed, failed).
    """
    passed = content.count("✅ pass")
    failed = content.count("❌ FAIL")
    return passed + failed, passed, failed


def _section_summary(p: dict[str, object]) -> str:
    """Return a one-line summary for a sub-report in the Executive Summary.

    Avoids meaningless ``0/0`` for reports that don't use ✅/❌ icons.

    Args:
        p: Per-report info dict from ``_collect_sections``.

    Returns:
        Human-readable summary string.
    """
    total = int(p.get("total", 0))
    passed = int(p.get("passed", 0))
    failed = int(p.get("failed", 0))
    if total == 0:
        return "inventory / metrics report"
    return f"{passed}/{total} checks passed" + (
        f", **{failed} failed**" if failed else ""
    )


def _make_header(
    now: str,
    parts: list[dict[str, object]],
    missing: list[str],
) -> str:
    """Return the frontmatter + title + Executive Summary block.

    Args:
        now: Timestamp string.
        parts: Per-report info dicts.
        missing: List of missing report filenames.

    Returns:
        A GFM string to prepend to the merged document.
    """
    total_passed = sum(
        int(p.get("passed", 0)) for p in parts if p.get("found")
    )
    total_failed = sum(
        int(p.get("failed", 0)) for p in parts if p.get("found")
    )
    overall = (
        "✅ ALL CHECKS PASSED"
        if total_failed == 0
        else f"❌ {total_failed} CHECK(S) FAILED"
    )

    lines = [
        "---",
        "title: Quality Report",
        f"date: {now}",
        f"description: Consolidated quality gate report — {_QC.project_name}.",
        "tags:",
        "  - quality",
        "  - ci",
        f"  - {_QC.project_name}",
        f"generator: {_QC.project_name}.report",
        "---",
        "",
        "# Quality Report",
        "",
        f"Generated: **{now}**",
        "",
        "## Executive Summary",
        "",
        f"**Overall result: {overall}**",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| ✅ Passed | {total_passed} |",
        f"| ❌ Failed | {total_failed} |",
        "",
    ]

    if missing:
        lines.append(
            "> **Warning:** reports not generated: "
            + ", ".join(f"`{m}`" for m in missing)
        )
        lines.append("")

    lines.append("### Sections in this document")
    lines.append("")
    for p in parts:
        fname = str(p["filename"])
        name = fname.replace("report_", "").replace(".md", "")
        if p.get("found"):
            icon = "❌" if int(p.get("failed", 0)) > 0 else "✅"
            summary = _section_summary(p)
            lines.append(f"- {icon} **{name}** — {summary}")
        else:
            lines.append(f"- ⚠️ **{name}** — not generated")
    lines.append("")
    return "\n".join(lines)


def _zip_artefacts() -> None:
    """Zip the consolidated report, individual reports, and native artefacts."""
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        # Main consolidated report
        if OUT_PATH.exists():
            zf.write(OUT_PATH, arcname="quality_report.md")

        # Individual section reports
        for p in sorted(REPORTS_DIR.rglob("*.md")):
            zf.write(p, arcname=f"reports/{p.name}")

        # Native artefacts (xml, interactive html coverage)
        for pattern in NATIVE_ARTEFACTS:
            path = Path(pattern)
            if path.exists():
                zf.write(path, arcname=f"native/{path.name}")

        # HTML coverage report (interactive, not duplicated in markdown)
        htmlcov = WORK / "htmlcov"
        if htmlcov.exists():
            for p in sorted(htmlcov.rglob("*")):
                if p.is_file():
                    zf.write(p, arcname=f"native/htmlcov/{p.name}")


def _cleanup() -> None:
    """Remove intermediate files that are now packed in the zip."""
    # Remove individual report files (now inside the zip)
    if REPORTS_DIR.exists():
        shutil.rmtree(REPORTS_DIR)
    # Remove log files (duplicated value inside the markdown reports)
    for log in WORK.glob("*.log"):
        log.unlink(missing_ok=True)
    # Remove native XML/MD artefacts (now inside the zip)
    for pattern in NATIVE_ARTEFACTS:
        path = Path(pattern)
        if path.exists():
            path.unlink()


if __name__ == "__main__":
    main()
