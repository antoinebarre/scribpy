"""Generate the test results and coverage report."""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from report_common import base_metadata

from scribpy.report import (
    BlockQuote,
    Chapter,
    CodeBlock,
    Paragraph,
    Report,
    Section,
    Table,
    Text,
    file_checksum,
)

WORK = Path("work")
JUNIT = WORK / "junit.xml"
COV_XML = WORK / "coverage.xml"
TESTS_LOG = WORK / "tests.log"
OUT_PATH = WORK / "reports" / "report_tests.md"


def main() -> None:
    """Build the test + coverage report."""
    test_data = _parse_junit(JUNIT)
    cov_data = _parse_coverage(COV_XML)

    total = test_data["total"]
    passed_n = test_data["passed"]
    failed_n = test_data["failed"]
    errors_n = test_data["errors"]
    skipped_n = test_data["skipped"]

    report = (
        Report(
            title="Test Results & Coverage",
            metadata=base_metadata("Test Results & Coverage", "tests"),
        )
        .add(
            Chapter(title="Summary")
            .add(
                Paragraph(
                    [
                        Text(f"{total}", style="bold"),
                        Text(" tests — "),
                        Text(f"{passed_n} passed", style="bold"),
                        Text(", "),
                        Text(f"{failed_n} failed" if failed_n else "0 failed"),
                        Text(f", {errors_n} error(s)" if errors_n else ""),
                        Text(f", {skipped_n} skipped" if skipped_n else ""),
                        Text(f" — duration: {test_data['duration']:.2f}s"),
                    ]
                )
            )
            .add(
                Paragraph(
                    [
                        Text("Overall coverage: "),
                        Text(f"{cov_data['total_pct']:.1f}%", style="bold"),
                        Text(
                            f" ({cov_data['covered']}"
                            f"/{cov_data['valid']} lines)"
                        ),
                    ]
                )
            )
        )
        .add(_test_results_chapter(test_data))
        .add(_coverage_chapter(cov_data))
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report.save(str(OUT_PATH))
    print(f"Written: {OUT_PATH}")


def _parse_junit(path: Path) -> dict[str, object]:
    if not path.exists():
        return {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
            "duration": 0.0,
            "by_module": {},
        }
    root = ET.parse(path).getroot()
    suite = list(root)[0] if root.tag == "testsuites" else root
    total = int(suite.attrib.get("tests", 0))
    failed = int(suite.attrib.get("failures", 0))
    errors = int(suite.attrib.get("errors", 0))
    skipped = int(suite.attrib.get("skipped", 0))
    passed = total - failed - errors - skipped
    duration = float(suite.attrib.get("time", 0))

    by_module: dict[str, list[dict[str, object]]] = {}
    for tc in suite.iter("testcase"):
        cls = tc.attrib.get("classname", "unknown")
        module = cls.rsplit(".", 1)[0] if "." in cls else cls
        status = "pass"
        msg = ""
        if tc.find("failure") is not None:
            status = "FAIL"
            msg = (tc.find("failure").attrib.get("message", ""))[:120]
        elif tc.find("error") is not None:
            status = "ERROR"
            msg = (tc.find("error").attrib.get("message", ""))[:120]
        elif tc.find("skipped") is not None:
            status = "skip"
        by_module.setdefault(module, []).append(
            {
                "name": tc.attrib.get("name", ""),
                "time": float(tc.attrib.get("time", 0)),
                "status": status,
                "message": msg,
            }
        )

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "skipped": skipped,
        "duration": duration,
        "by_module": by_module,
    }


def _parse_coverage(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"total_pct": 0.0, "covered": 0, "valid": 0, "files": []}
    root = ET.parse(path).getroot()
    valid = int(root.attrib.get("lines-valid", 0))
    covered = int(root.attrib.get("lines-covered", 0))
    total_pct = float(root.attrib.get("line-rate", 0)) * 100

    files: list[dict[str, object]] = []
    for cls in root.iter("class"):
        filename = cls.attrib.get("filename", "")
        rate = float(cls.attrib.get("line-rate", 1)) * 100
        missing = [
            str(ln.attrib["number"])
            for ln in cls.iter("line")
            if ln.attrib.get("hits", "1") == "0"
        ]
        files.append({"file": filename, "pct": rate, "missing": missing})
    files.sort(key=lambda f: f["pct"])
    return {
        "total_pct": total_pct,
        "covered": covered,
        "valid": valid,
        "files": files,
    }


def _test_results_chapter(data: dict[str, object]) -> Chapter:
    chapter = Chapter(title="Test Results by Module")
    by_module: dict[str, list[dict[str, object]]] = data["by_module"]  # type: ignore[assignment]

    for module, cases in sorted(by_module.items()):
        module_pass = sum(1 for c in cases if c["status"] == "pass")
        module_fail = sum(1 for c in cases if c["status"] in ("FAIL", "ERROR"))
        header = f"{module} — {module_pass}/{len(cases)} passed"

        try:
            src_path = Path("tests") / Path(*module.split(".")[1:])
            src_path = src_path.with_suffix(".py")
            chk = file_checksum(src_path) if src_path.exists() else "n/a"
        except Exception:
            chk = "n/a"

        section = Section(title=header)
        rows = [
            [
                c["name"],  # type: ignore[index]
                c["status"],  # type: ignore[index]
                f"{float(c['time']):.3f}s",  # type: ignore[arg-type]
                c["message"] or "",  # type: ignore[index,operator]
            ]
            for c in cases
        ]
        section.add(
            Paragraph(
                [
                    Text("Test file SHA-256: "),
                    Text(chk, style="code"),
                ]
            )
        )
        section.add(
            Table(
                headers=["Test", "Result", "Duration", "Message"],
                rows=rows,
            )
        )

        if module_fail:
            section.add(
                BlockQuote(f"{module_fail} test(s) failed in this module.")
            )
        chapter.add(section)
    return chapter


def _coverage_chapter(data: dict[str, object]) -> Chapter:
    chapter = Chapter(title="Coverage by File")
    files: list[dict[str, object]] = data["files"]  # type: ignore[assignment]

    rows = []
    for f in files:
        pct = float(f["pct"])  # type: ignore[arg-type]
        missing = f["missing"]  # type: ignore[assignment]
        missing_str = ", ".join(missing[:10]) + (  # type: ignore[arg-type]
            "…" if len(missing) > 10 else ""
        )
        rows.append([str(f["file"]), f"{pct:.0f}%", missing_str or "—"])

    chapter.add(
        Paragraph(
            [
                Text("Coverage data from "),
                Text("work/coverage.xml", style="code"),
                Text(". Lines shown are not executed during the test suite."),
            ]
        )
    )
    chapter.add(
        Table(
            headers=["File", "Coverage", "Uncovered lines"],
            rows=rows,
        )
    )
    chapter.add(_pytest_log_section())
    return chapter


def _pytest_log_section() -> Section:
    """Build a Section with the reformatted pytest console output.

    Returns:
        A ``Section`` containing the pytest stdout as a code block,
        with the verbose file-by-file listing stripped to keep only
        the summary lines (totals, coverage table, errors).
    """
    if not TESTS_LOG.exists():
        return Section(title="Pytest Output").add(
            Paragraph("Log file not found.")
        )
    raw = TESTS_LOG.read_text(encoding="utf-8", errors="replace")
    cleaned = _clean_pytest_log(raw)
    return Section(title="Pytest Console Output").add(
        CodeBlock(code=cleaned, language="")
    )


def _clean_pytest_log(raw: str) -> str:
    """Strip the verbose per-test dots/lines, keep summary + coverage table.

    Args:
        raw: Full pytest stdout text.

    Returns:
        Cleaned text with only the meaningful output.
    """
    lines = raw.splitlines()
    kept: list[str] = []
    in_coverage = False

    for line in lines:
        # Coverage table starts here
        if re.match(r"^-+\s+coverage", line, re.IGNORECASE):
            in_coverage = True
        if in_coverage:
            kept.append(line)
            continue
        # Keep: header, errors, warnings, summary, passed/failed line
        if re.match(
            r"^(=====|-----|\d+ passed|\d+ failed|FAILED|ERROR"
            r"|platform |collected |tests/|WARNING|ERRORS)",
            line,
        ):
            kept.append(line)
    return "\n".join(kept) if kept else raw[:4000]


if __name__ == "__main__":
    main()
