"""Demo script for the scribpy Report Generator API.

Mirrors the structure of demo_API.py: output goes to work/report-demo/.
Exercises every node type — including ImageFile (user-supplied images
copied alongside the output) — without requiring any third-party library.

Run:
    python3 demo_report.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from scribpy.report import (
    BlockQuote,
    BulletList,
    Chapter,
    CodeBlock,
    HorizontalRule,
    ImageFile,
    LineBreak,
    Metadata,
    NumberedList,
    Paragraph,
    Report,
    Section,
    Table,
    Text,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent
OUTPUT_DIR = REPO_ROOT / "work" / "report-demo"

# PNG fixtures shipped with the repo — no matplotlib required.
FIXTURES = REPO_ROOT / "tests" / "fixtures"
CHART_LINE = str(FIXTURES / "chart_line.png")
CHART_BAR = str(FIXTURES / "chart_bar.png")
CHART_SCATTER = str(FIXTURES / "chart_scatter.png")


def main() -> None:
    """Build three demo reports and print a summary."""
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    _section("Report Generator Demo")

    report_basic = _build_basic_report()
    out_basic = OUTPUT_DIR / "basic_report.md"
    report_basic.save(str(out_basic))
    _step("Basic report (all node types)", out_basic.exists())

    report_toc = _build_toc_report()
    out_toc = OUTPUT_DIR / "toc_report.md"
    report_toc.save(str(out_toc))
    _step("Report with table of contents", out_toc.exists())

    report_numbered = _build_numbered_report()
    out_numbered = OUTPUT_DIR / "numbered_report.md"
    report_numbered.save(str(out_numbered))
    _step("Report with auto-numbering + embedded images", out_numbered.exists())

    print()
    _section("Output files")
    for p in sorted(OUTPUT_DIR.rglob("*")):
        if p.is_file():
            print(f"  {p}")

    print()
    _section("Preview: numbered_report.md")
    print(report_numbered.render())


# ---------------------------------------------------------------------------
# Report builders
# ---------------------------------------------------------------------------

def _build_basic_report() -> Report:
    """Build a report that exercises every node type."""
    return (
        Report(
            title="Scribpy Report Generator — Feature Overview",
            metadata=Metadata(
                author="Antoine Barré",
                date="2026-05-20",
                version="1.0",
                description="Demonstration of every node type in scribpy.report.",
                tags=["scribpy", "demo", "markdown"],
            ),
        )
        .add(
            Chapter(title="Introduction")
            .add(
                Paragraph([
                    Text("This report demonstrates "),
                    Text("every node type", style="bold"),
                    Text(" available in the "),
                    Text("scribpy.report", style="code"),
                    Text(" API."),
                ])
            )
            .add(
                Paragraph([
                    Text("Line one of a paragraph."),
                    LineBreak(),
                    Text("Line two — same block, hard line break."),
                    LineBreak(),
                    Text("Line three — still in the same paragraph."),
                ])
            )
            .add(BlockQuote(
                "Design goal: compose reports in pure Python,\n"
                "export to GitHub Flavored Markdown."
            ))
        )
        .add(
            Chapter(title="Formatting")
            .add(
                Section(title="Inline styles")
                .add(Paragraph([
                    Text("plain "),
                    Text("bold", style="bold"),
                    Text(" "),
                    Text("italic", style="italic"),
                    Text(" "),
                    Text("inline_code()", style="code"),
                    Text(" "),
                    Text("struck", style="strikethrough"),
                ]))
            )
            .add(
                Section(title="Lists")
                .add(BulletList(items=["Alpha", "Beta", "Gamma"]))
                .add(NumberedList(items=["First step", "Second step", "Third step"]))
            )
            .add(
                Section(title="Code")
                .add(CodeBlock(
                    code=(
                        "from scribpy.report import Report, Chapter\n\n"
                        "r = Report(title='Hello')\n"
                        "r.add(Chapter(title='World'))\n"
                        "r.save('output/report.md')"
                    ),
                    language="python",
                ))
            )
            .add(
                Section(title="Table")
                .add(Table(
                    headers=["Node", "GFM output", "Notes"],
                    rows=[
                        ["Text(bold)", "**text**", "inline"],
                        ["CodeBlock", "``` … ```", "fenced block"],
                        ["Table", "| … |", "pipe syntax"],
                        ["ImageFile", "![alt](assets/…)", "copied on save"],
                    ],
                ))
            )
        )
        .add(
            Chapter(title="Media")
            .add(
                Section(title="User-supplied image")
                .add(Paragraph(
                    "The image below is copied from its source location "
                    "into the assets/ directory alongside the .md file."
                ))
                .add(ImageFile(
                    source_path=CHART_LINE,
                    alt="Line chart",
                    caption="Figure 1 — example user-supplied image (copied on save).",
                ))
            )
            .add(HorizontalRule())
            .add(Paragraph("End of feature overview."))
        )
    )


def _build_toc_report() -> Report:
    """Build a report with an auto-generated table of contents."""
    return (
        Report(
            title="Report With Table of Contents",
            toc=True,
            metadata=Metadata(
                author=["Alice Martin", "Bob Dupont"],
                date="2026-05-20",
                description="Quarterly results with auto-generated TOC.",
                tags=["results", "quarterly"],
                extra={"status": "draft", "lang": "en"},
            ),
        )
        .add(
            Chapter(title="Introduction")
            .add(Paragraph("Overview of the document."))
            .add(Section(title="Background").add(Paragraph("Historical context.")))
            .add(Section(title="Objectives").add(Paragraph("Goals for this cycle.")))
        )
        .add(
            Chapter(title="Results")
            .add(
                Section(title="Quantitative")
                .add(Table(
                    headers=["KPI", "Target", "Actual"],
                    rows=[
                        ["Uptime", "99.9 %", "99.95 %"],
                        ["Latency p99", "200 ms", "185 ms"],
                    ],
                ))
            )
            .add(
                Section(title="Qualitative")
                .add(BlockQuote("Customer satisfaction improved significantly."))
            )
        )
        .add(
            Chapter(title="Conclusion")
            .add(Paragraph("All targets were met or exceeded."))
        )
    )


def _build_numbered_report() -> Report:
    """Build a numbered report with embedded user-supplied images."""
    return (
        Report(
            title="Quarterly Analysis Report",
            auto_numbering=True,
            toc=True,
            metadata=Metadata(
                author="Antoine Barré",
                date="2026-05-20",
                version="2.1",
                description="Q1 2026 performance — throughput, latency, errors.",
                tags=["performance", "Q1-2026", "analysis"],
                extra={"classification": "internal", "review": "pending"},
            ),
        )
        .add(
            Chapter(title="Executive Summary")
            .add(Paragraph([
                Text("This report covers "),
                Text("Q1 2026", style="bold"),
                Text(" performance across three dimensions: throughput,"),
                LineBreak(),
                Text("latency, and error rate."),
            ]))
            .add(Table(
                headers=["Metric", "Q4 2025", "Q1 2026", "Delta"],
                rows=[
                    ["Throughput (req/s)", "1 200", "1 580", "+32 %"],
                    ["Latency p99 (ms)", "210", "185", "-12 %"],
                    ["Error rate", "0.8 %", "0.3 %", "-63 %"],
                ],
            ))
        )
        .add(
            Chapter(title="Throughput Analysis")
            .add(Paragraph("Monthly throughput over the quarter showed consistent growth."))
            .add(ImageFile(
                source_path=CHART_LINE,
                alt="Monthly throughput chart",
                caption="Figure 1 — Monthly throughput (req/s), Q1 2026.",
            ))
            .add(
                Section(title="Peak Days")
                .add(Paragraph([
                    Text("The three highest-traffic days were "),
                    Text("March 15, 22, and 28", style="bold"),
                    Text(", each exceeding "),
                    Text("2 000 req/s", style="code"),
                    Text("."),
                ]))
                .add(BulletList(items=[
                    "March 15 — product launch event",
                    "March 22 — marketing campaign",
                    "March 28 — end-of-quarter batch jobs",
                ]))
            )
            .add(
                Section(title="Root Cause")
                .add(
                    Section(title="Infrastructure changes")
                    .add(Paragraph("Two additional replicas were added on March 10."))
                )
                .add(
                    Section(title="Code optimisation")
                    .add(CodeBlock(
                        code=(
                            "# Hot path: O(n²) → O(n log n)\n"
                            "result = sorted(items, key=lambda x: x.score)"
                        ),
                        language="python",
                    ))
                )
            )
        )
        .add(
            Chapter(title="Latency Distribution")
            .add(Paragraph("The chart below shows p50/p95/p99 latency per service."))
            .add(ImageFile(
                source_path=CHART_BAR,
                alt="Latency per service",
                caption="Figure 2 — p50 / p95 / p99 latency breakdown.",
            ))
        )
        .add(
            Chapter(title="Error Analysis")
            .add(Paragraph("Scatter plot of error rate vs. request volume per endpoint."))
            .add(ImageFile(
                source_path=CHART_SCATTER,
                alt="Error rate scatter",
                caption="Figure 3 — Error rate vs. request volume.",
            ))
            .add(
                Section(title="Action Items")
                .add(NumberedList(items=[
                    "Investigate endpoint /api/export (high error rate at low volume)",
                    "Add circuit breaker for /api/batch",
                    "Review timeout settings for /api/search",
                ]))
            )
        )
        .add(
            Chapter(title="Appendix")
            .add(HorizontalRule())
            .add(Paragraph([
                Text("Images embedded via "),
                Text("ImageFile", style="code"),
                Text(" — copied into "),
                Text("assets/", style="code"),
                Text(" on save."),
            ]))
        )
    )


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _section(title: str) -> None:
    print(title)
    print("─" * len(title))


def _step(label: str, succeeded: bool) -> None:
    mark = "✔" if succeeded else "✘"
    status = "done" if succeeded else "failed"
    print(f"{mark} {label} — {status}")


if __name__ == "__main__":
    main()
