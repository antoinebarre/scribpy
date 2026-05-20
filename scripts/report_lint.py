"""Generate compliance report: lint, type-check, security, config, exceptions."""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from report_common import base_metadata

from scribpy.report import (
    BulletList,
    Chapter,
    CodeBlock,
    HorizontalRule,
    Paragraph,
    Report,
    Section,
    Table,
    Text,
)

WORK = Path("work")
OUT_PATH = WORK / "reports" / "report_lint.md"
PYPROJECT = Path("pyproject.toml")

# GitHub/GitLab GFM: emoji symbols render as coloured icons natively
PASS_ICON = "✅ pass"
FAIL_ICON = "❌ FAIL"

SUCCESS_PATTERNS: dict[str, re.Pattern[str]] = {
    "format": re.compile(r"\d+ files? (?:left unchanged|reformatted)"),
    "lint": re.compile(r"All checks passed!"),
    "docstrings": re.compile(r"All checks passed!"),
    "docstrings-strict": re.compile(r"Strict Google docstring check passed"),
    "init-modules": re.compile(r"Initializer module check passed"),
    "type-check": re.compile(r"Success: no issues found in \d+ source files"),
    "metrics": re.compile(r"Code metrics passed"),
    "security-code": re.compile(r"No issues identified"),
    "security-deps": re.compile(r"No known vulnerabilities found"),
}

CODE_QUALITY_CHECKS: list[tuple[str, str]] = [
    ("format", "Code Formatting (ruff format)"),
    ("lint", "Lint Rules (ruff check)"),
    ("docstrings", "Docstring Presence (ruff D)"),
    ("docstrings-strict", "Google Docstring Style"),
    ("init-modules", "Init Module Compliance"),
    ("type-check", "Static Type Check (mypy)"),
    ("metrics", "Code Metrics"),
]

SECURITY_CHECKS: list[tuple[str, str]] = [
    ("security-code", "SAST — Source Code (bandit)"),
    ("security-deps", "SCA — Dependencies (pip-audit)"),
]


def _load_pyproject() -> dict[str, object]:
    if not PYPROJECT.exists():
        return {}
    with PYPROJECT.open("rb") as f:
        return tomllib.load(f)


def _log_path(name: str) -> Path:
    """Resolve log file with fallback for ci.sh hyphen-free naming.

    Args:
        name: Check identifier (e.g. ``"type-check"``).

    Returns:
        Resolved log file path.
    """
    primary = WORK / f"{name}.log"
    if primary.exists():
        return primary
    fallback = WORK / f"{name.replace('-', '')}.log"
    return fallback if fallback.exists() else primary


def _is_passed(name: str, body: str) -> bool:
    """Return True when body matches the per-check success pattern.

    Args:
        name: Check identifier.
        body: Full log text.

    Returns:
        ``True`` if the check passed.
    """
    pattern = SUCCESS_PATTERNS.get(name)
    return bool(pattern.search(body)) if pattern else False


def _extract_summary(name: str, body: str) -> str:
    """Extract a short summary line from the log for the overview table.

    Args:
        name: Check identifier.
        body: Full log text.

    Returns:
        A short summary string (max 120 chars).
    """
    patterns: dict[str, str] = {
        "format": r"(\d+ files? (?:left unchanged|reformatted))",
        "lint": r"(All checks passed!|Found \d+ errors?\.)",
        "docstrings": r"(All checks passed!|Found \d+ errors?\.)",
        "docstrings-strict": r"(Strict Google docstring check (?:passed|failed).*)",
        "init-modules": r"(Initializer module check (?:passed|failed).*)",
        "type-check": r"(Success: .*|Found \d+ errors? in \d+ file)",
        "metrics": r"(Code metrics (?:passed|failed).*)",
        "security-code": r"(No issues identified\.?|Issue\[.*\])",
        "security-deps": r"(No known vulnerabilities found.*|Found \d+ known)",
    }
    pat = patterns.get(name)
    if pat:
        m = re.search(pat, body)
        if m:
            return m.group(1).strip()
    last = [ln.strip() for ln in body.splitlines() if ln.strip()]
    return last[-1][:120] if last else ""


def _issue_filter(name: str) -> re.Pattern[str] | None:
    """Return a per-check pattern matching actual problem lines, or None.

    Args:
        name: Check identifier.

    Returns:
        Compiled regex or ``None`` if no per-line extraction applies.
    """
    patterns: dict[str, str] = {
        "lint": r"\s*(E|W|F|D)\d+",
        "docstrings": r"\s*(E|W|F|D)\d+",
        "docstrings-strict": r".+:\s*\w+ missing \w+",
        "init-modules": r".*\.py.*missing|.*ERROR.*",
        "type-check": r": error:|: note:",
        "security-code": r"Issue:|Severity:",
        "security-deps": r"PYSEC|vulnerability",
    }
    raw = patterns.get(name)
    return re.compile(raw, re.IGNORECASE) if raw else None


def _extract_issues(name: str, body: str) -> list[str]:
    """Extract actionable issue lines from the log.

    Args:
        name: Check identifier.
        body: Full log text.

    Returns:
        List of issue lines (may be empty).
    """
    pattern = _issue_filter(name)
    if pattern is None:
        return []
    return [ln for ln in body.splitlines() if pattern.search(ln)]


def _parse_check(name: str, title: str) -> dict[str, object]:
    """Read and parse a single check log file.

    Args:
        name: Check identifier.
        title: Human-readable title.

    Returns:
        Dict with keys: name, title, passed, summary, body.
    """
    log = _log_path(name)
    if not log.exists():
        return {
            "name": name,
            "title": title,
            "passed": False,
            "summary": "log not found",
            "body": "",
        }
    body = log.read_text(encoding="utf-8", errors="replace")
    return {
        "name": name,
        "title": title,
        "passed": _is_passed(name, body),
        "summary": _extract_summary(name, body),
        "body": body,
    }


def _summary_table(results: list[dict[str, object]]) -> Table:
    """Build a Check | Status | Detail table for results.

    Args:
        results: Parsed check result dicts.

    Returns:
        A ``Table`` node.
    """
    return Table(
        headers=["Check", "Status", "Detail"],
        rows=[
            [r["title"], PASS_ICON if r["passed"] else FAIL_ICON, r["summary"]]
            for r in results
        ],
    )


def _ruff_exceptions(tool: dict[str, object]) -> list[str]:
    """Extract ruff ignore/exclude exceptions from pyproject tool config.

    Args:
        tool: The ``[tool]`` table from pyproject.toml.

    Returns:
        List of human-readable exception strings.
    """
    ruff = tool.get("ruff", {})  # type: ignore[union-attr]
    lint = ruff.get("lint", {})  # type: ignore[union-attr]
    items: list[str] = []
    for r in lint.get("ignore", []):
        items.append(f"Global ignore: `{r}`")
    for pat, codes in lint.get("per-file-ignores", {}).items():
        items.append(f"`{pat}`: ignore {', '.join(f'`{c}`' for c in codes)}")
    for p in ruff.get("exclude", []):
        items.append(f"Excluded path: `{p}`")
    return items


def _mypy_exceptions(tool: dict[str, object]) -> list[str]:
    """Extract mypy override exceptions from pyproject tool config.

    Args:
        tool: The ``[tool]`` table from pyproject.toml.

    Returns:
        List of human-readable exception strings.
    """
    mypy = tool.get("mypy", {})  # type: ignore[union-attr]
    items: list[str] = []
    for ov in mypy.get("overrides", []):
        mods = ov.get("module", "")
        if ov.get("ignore_missing_imports"):
            items.append(f"ignore_missing_imports: `{mods}`")
        if ov.get("ignore_errors"):
            items.append(f"ignore_errors: `{mods}`")
    return items


def _bandit_exceptions(tool: dict[str, object]) -> list[str]:
    """Extract bandit skip/exclude exceptions from pyproject tool config.

    Args:
        tool: The ``[tool]`` table from pyproject.toml.

    Returns:
        List of human-readable exception strings.
    """
    bandit = tool.get("bandit", {})  # type: ignore[union-attr]
    items = [f"Skipped test: `{s}`" for s in bandit.get("skips", [])]
    items += [f"Excluded dir: `{d}`" for d in bandit.get("exclude_dirs", [])]
    return items


def _pip_audit_exceptions(tool: dict[str, object]) -> list[str]:
    """Extract pip-audit ignored vulnerability exceptions from pyproject.

    Args:
        tool: The ``[tool]`` table from pyproject.toml.

    Returns:
        List of human-readable exception strings.
    """
    sec = tool.get("scribpy", {}).get("security_audit", {})  # type: ignore[union-attr]
    return [
        f"Ignored vulnerability: `{v}`" for v in sec.get("ignore_vulns", [])
    ]


def _exceptions_section(
    name: str, config: dict[str, object]
) -> Section | None:
    """Build a Section listing configured exceptions for a check.

    Args:
        name: Check identifier.
        config: Parsed pyproject.toml data.

    Returns:
        A ``Section`` node or ``None`` if no exceptions are configured.
    """
    tool = config.get("tool", {})
    extractor = {
        "lint": _ruff_exceptions,
        "docstrings": _ruff_exceptions,
        "format": _ruff_exceptions,
        "type-check": _mypy_exceptions,
        "security-code": _bandit_exceptions,
        "security-deps": _pip_audit_exceptions,
    }.get(name)
    if extractor is None:
        return None
    items = extractor(tool)  # type: ignore[arg-type]
    if not items:
        return None
    return Section(title="Configured Exceptions").add(BulletList(items=items))


def _config_section(name: str, config: dict[str, object]) -> Section | None:
    """Build a Section showing the tool configuration for a check.

    Args:
        name: Check identifier.
        config: Parsed pyproject.toml data.

    Returns:
        A ``Section`` node or ``None`` if no config is available.
    """
    tool = config.get("tool", {})
    rows: list[list[str]] = []

    if name in ("lint", "format", "docstrings"):
        ruff = tool.get("ruff", {})  # type: ignore[union-attr]
        lint = ruff.get("lint", {})
        selected = lint.get("select", [])
        line_len = ruff.get("line-length", 88)
        rows = [
            ["line-length", str(line_len)],
            [
                "select",
                ", ".join(f"`{r}`" for r in selected)
                if selected
                else "default",
            ],
        ]

    elif name == "type-check":
        mypy = tool.get("mypy", {})  # type: ignore[union-attr]
        rows = [
            [k, str(v)]
            for k, v in mypy.items()
            if k not in ("overrides",) and not isinstance(v, (list, dict))
        ]

    elif name == "metrics":
        metrics = tool.get("scribpy", {}).get("code_metrics", {})  # type: ignore[union-attr]
        rows = [
            [k, str(v)]
            for k, v in metrics.items()
            if k not in ("paths", "exclude")
        ]

    elif name == "security-code":
        bandit = tool.get("bandit", {})  # type: ignore[union-attr]
        rows = [[k, str(v)] for k, v in bandit.items()]

    elif name == "security-deps":
        rows = [["tool", "pip-audit"], ["format", "freeze"]]

    if not rows:
        return None
    return Section(title="Configuration").add(
        Table(headers=["Parameter", "Value"], rows=rows)
    )


def _details_section(
    result: dict[str, object],
    config: dict[str, object],
) -> Section:
    """Build a full detail Section for one check result.

    Args:
        result: Parsed check result dict.
        config: Parsed pyproject.toml data.

    Returns:
        A populated ``Section`` node.
    """
    body = str(result["body"]).strip()
    icon = PASS_ICON if result["passed"] else FAIL_ICON
    section = Section(title=str(result["title"])).add(
        Paragraph([Text(f"Status: {icon}", style="bold")])
    )

    cfg_sec = _config_section(str(result["name"]), config)
    if cfg_sec:
        section.add(cfg_sec)

    exc_sec = _exceptions_section(str(result["name"]), config)
    if exc_sec:
        section.add(exc_sec)

    issues = _extract_issues(str(result["name"]), body)
    if issues:
        section.add(Section(title="Issues").add(BulletList(items=issues[:50])))
    if not result["passed"]:
        section.add(
            Section(title="Full Output").add(
                CodeBlock(code=body[:3000], language="")
            )
        )
    section.add(HorizontalRule())
    return section


def _build_chapter(
    chapter_title: str,
    checks: list[tuple[str, str]],
    config: dict[str, object],
) -> tuple[Chapter, list[dict[str, object]]]:
    """Build a Chapter with summary table and per-check detail sections.

    Args:
        chapter_title: Chapter heading.
        checks: List of (name, title) pairs.
        config: Parsed pyproject.toml.

    Returns:
        Tuple of (Chapter node, result dicts).
    """
    results = [_parse_check(name, title) for name, title in checks]
    passed = sum(1 for r in results if r["passed"])
    failed = len(results) - passed

    chapter = Chapter(title=chapter_title)
    chapter.add(
        Paragraph(
            [
                Text(f"{passed}", style="bold"),
                Text(" checks passed, "),
                Text(f"{failed}", style="bold"),
                Text(" failed."),
            ]
        )
    )
    chapter.add(_summary_table(results))
    for result in results:
        chapter.add(_details_section(result, config))
    return chapter, results


def main() -> None:
    """Build the compliance report from all log files."""
    config = _load_pyproject()
    code_chapter, code_results = _build_chapter(
        "Code Quality Compliance", CODE_QUALITY_CHECKS, config
    )
    sec_chapter, sec_results = _build_chapter(
        "Security Compliance", SECURITY_CHECKS, config
    )

    all_results = code_results + sec_results
    total_passed = sum(1 for r in all_results if r["passed"])
    total_failed = len(all_results) - total_passed

    report = (
        Report(
            title="Compliance Report",
            metadata=base_metadata("Compliance Report", "lint"),
        )
        .add(
            Chapter(title="Summary")
            .add(
                Paragraph(
                    [
                        Text(f"{total_passed}", style="bold"),
                        Text(" checks passed, "),
                        Text(f"{total_failed}", style="bold"),
                        Text(" failed."),
                    ]
                )
            )
            .add(_summary_table(all_results))
        )
        .add(code_chapter)
        .add(sec_chapter)
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report.save(str(OUT_PATH))
    print(f"Written: {OUT_PATH}")


if __name__ == "__main__":
    main()
