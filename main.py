"""Small executable example of Scribpy's public Python API."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

# Allow `python main.py` from the repository root without installing the package.
sys.path.insert(0, str(Path(__file__).parent / "src"))

import scribpy

PLANTUML_SERVER_URL = "http://www.plantuml.com/plantuml"


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

        # Write the extra blue theme after create_demo so it survives the wipe.
        _write_blue_theme(demo_dir / "theme" / "blue.css")

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
        web_html_result = scribpy.build_html(
            demo_dir,
            mode="single-page",
            extra_css=["theme/blue.css"],
        )
        # java_html_result = scribpy.build_html(
        #     demo_dir,
        #     mode="single-page",
        #     extra_css=["theme/blue.css"],
        #     plantuml_renderer="java",
        # )
        web_site_result = scribpy.build_html(
            demo_dir,
            mode="site",
            plantuml_renderer="web",
            plantuml_server_url=PLANTUML_SERVER_URL,
        )

    _step("Build Markdown", markdown_result.success)
    _step("Build HTML single-page with default web PlantUML", web_html_result.success)
    #_step("Build HTML single-page with forced Java PlantUML", java_html_result.success)
    _step("Build HTML site with forced web PlantUML", web_site_result.success)
    _artifact_summary("Markdown", markdown_result)
    _artifact_summary("HTML single-page (web)", web_html_result)
    #_artifact_summary("HTML single-page (java)", java_html_result)
    _artifact_summary("HTML site (web)", web_site_result)
    _print_failure_details("HTML single-page (web)", web_html_result)
    #_print_failure_details("HTML single-page (java)", java_html_result)
    _print_failure_details("HTML site (web)", web_site_result)

    # A second demo shows what callers receive when linting fails.
    if invalid_dir.exists():
        shutil.rmtree(invalid_dir)
    scribpy.create_demo(invalid_dir, variant="invalid")
    invalid_lint = scribpy.lint(invalid_dir)

    _section("Invalid project diagnostics")
    _step("Run lint rules", not invalid_lint.failed)
    scribpy.print_result(invalid_lint)


def _write_blue_theme(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """\
/* ── Professional blue theme override ──────────────────────────────────── */
:root {
  --bg:           #f0f4ff;
  --surface:      #ffffff;
  --surface-soft: #e8eeff;
  --text:         #1a2340;
  --muted:        #5a6a8a;
  --heading:      #0d1b3e;
  --accent:       #1a56db;
  --accent-soft:  #dce8fd;
  --border:       #b8c8e8;
  --shadow:       0 18px 45px rgba(13, 27, 62, 0.10);
}

body {
  background:
    radial-gradient(ellipse at top left,  rgba(26, 86, 219, 0.14) 0%, transparent 38%),
    radial-gradient(ellipse at bottom right, rgba(99, 102, 241, 0.08) 0%, transparent 40%),
    var(--bg);
}

.document-content {
  border-color: rgba(184, 200, 232, 0.9);
  border-radius: 1.25rem;
}

.document-content h1 { color: #1e3a8a; letter-spacing: -0.045em; }
.document-content h2 { border-top-color: #bfdbfe; color: #1e40af; }
.document-content h3 { color: #0369a1; }
.document-content h4 { color: #3b5fa0; }

a       { color: var(--accent); }
a:hover { color: #1346b8; text-decoration-thickness: 0.12em; }

.document-content code { background: #dce8fd; color: #1e3a8a; }
.document-content pre  { background: #0d1b3e; }

.toc-panel    { background: rgba(240, 244, 255, 0.92) !important;
                border-right-color: rgba(184, 200, 232, 0.85) !important; }
.toc-eyebrow  { color: #3b5fa0; }
.toc-search:focus { border-color: var(--accent);
                    outline: 2px solid rgba(26, 86, 219, 0.25);
                    outline-offset: 1px; }
.toc-list a                        { color: var(--muted); }
.toc-list a:hover,
.toc-list a[aria-current="true"]   { background: var(--accent-soft);
                                     border-color: var(--accent);
                                     color: var(--heading); }
.toc-list a[aria-current="location"] { border-color: #93c5fd;
                                       color: #1d4ed8; }
.toc-toggle { background: #0d1b3e !important; }
""",
        encoding="utf-8",
    )


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


def _print_failure_details(label: str, result: scribpy.BuildResult) -> None:
    """Print diagnostics for one failed demo build.

    Args:
        label: Human-readable build label.
        result: Build result returned by Scribpy.
    """
    if result.success:
        return
    print(f"\n{label} diagnostics")
    scribpy.print_result(result)


if __name__ == "__main__":
    main()
