"""Single-page HTML builder."""

from __future__ import annotations

import re
from pathlib import Path

from scribpy.builders.html_single_page_assets import toc_script, toc_styles
from scribpy.model import BuildArtifact, Diagnostic
from scribpy.model.protocols import FileSystem

_HTML_OUTPUT_PATH = Path("index.html")
_ASSETS_DIR = Path("assets")
_SCRIPT_OUTPUT_PATH = Path("js/toc.js")

_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$", re.MULTILINE)
_LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")
_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


def render_markdown_to_html(content: str) -> str:
    """Convert Markdown content to HTML using lightweight built-in rendering.

    Args:
        content: Markdown text to render.

    Returns:
        HTML string without surrounding ``<html>`` scaffolding.
    """
    html_lines: list[str] = []
    code_lines: list[str] = []
    code_lang = ""
    in_code_block = False

    for line in content.split("\n"):
        if line.startswith("```"):
            in_code_block, code_lines, code_lang = _handle_fence(
                line, in_code_block, code_lines, code_lang, html_lines
            )
            continue
        if in_code_block:
            code_lines.append(line)
            continue
        html_lines.append(_render_block_line(line))

    return "\n".join(html_lines)


def _handle_fence(
    line: str,
    in_code_block: bool,
    code_lines: list[str],
    code_lang: str,
    html_lines: list[str],
) -> tuple[bool, list[str], str]:
    """Toggle code fence state and emit a block when closing.

    Args:
        line: Current line starting with backtick fence.
        in_code_block: Whether we are currently inside a code block.
        code_lines: Lines accumulated inside the current code block.
        code_lang: Language tag of the current code block.
        html_lines: Accumulated HTML output lines (mutated in place).

    Returns:
        Updated ``(in_code_block, code_lines, code_lang)`` triple.
    """
    if in_code_block:
        escaped = "\n".join(_escape(ln) for ln in code_lines)
        lang_attr = f' class="language-{code_lang}"' if code_lang else ""
        html_lines.append(f"<pre><code{lang_attr}>{escaped}</code></pre>")
        return False, [], ""
    return True, [], line[3:].strip()


def _render_block_line(line: str) -> str:
    """Convert one non-code Markdown line to its HTML equivalent.

    Args:
        line: A single Markdown line outside any code fence.

    Returns:
        HTML representation of the line.
    """
    heading_match = _HEADING_RE.match(line)
    if heading_match:
        marks, title = heading_match.groups()
        level = len(marks)
        return f'<h{level} id="{_anchor(title)}">{_inline(title)}</h{level}>'
    if line.startswith("---") and line.strip("-") == "":
        return "<hr>"
    stripped = line.strip()
    return f"<p>{_inline(stripped)}</p>" if stripped else ""


def build_single_page_html(
    body_html: str,
    title: str,
    css_hrefs: list[str],
) -> str:
    """Wrap an HTML body fragment in a full HTML5 document.

    Args:
        body_html: HTML body content to embed.
        title: Document title written into ``<title>``.
        css_hrefs: List of CSS hrefs to include as ``<link>`` elements.

    Returns:
        Complete HTML5 document as a string.
    """
    link_tags = "\n    ".join(
        f'<link rel="stylesheet" href="{href}">' for href in css_hrefs
    )
    prefix = "\n    " if link_tags else ""
    body_html = _remove_generated_markdown_toc(body_html)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{_escape(title)}</title>{prefix}{link_tags}
  <style>{toc_styles()}</style>
</head>
<body class="scribpy-document">
<button class="toc-toggle" type="button" aria-controls="page-toc"
        aria-expanded="false" aria-label="Toggle table of contents">
  <span class="toc-hamburger" aria-hidden="true"></span>
</button>
<div class="page-shell">
  <aside class="toc-panel" aria-label="Table of contents">
    <p class="toc-eyebrow">On this page</p>
    <label class="toc-search-label" for="toc-search">Filter sections</label>
    <input id="toc-search" class="toc-search" type="search"
           placeholder="Search headings">
    <nav id="page-toc" class="page-toc"></nav>
  </aside>
  <main class="document-content">
{body_html}
  </main>
</div>
<script src="js/toc.js"></script>
</body>
</html>
"""


def write_single_page_artifact(
    project_root: Path,
    html: str,
    output_dir: Path,
    filesystem: FileSystem,
) -> tuple[BuildArtifact | None, tuple[Diagnostic, ...]]:
    """Write the single-page HTML artifact to disk.

    Args:
        project_root: Absolute project root directory.
        html: Complete HTML document content.
        output_dir: Relative output directory (e.g. ``build/html``).
        filesystem: Filesystem service used for writing.

    Returns:
        Artifact descriptor on success, plus any write diagnostics.
    """
    artifact_path = project_root / output_dir / _HTML_OUTPUT_PATH
    try:
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        filesystem.write_text(artifact_path, html)
    except Exception as exc:
        return None, (
            Diagnostic(
                severity="error",
                code="BLD005",
                message=f"Cannot write HTML artifact: {exc}",
                path=artifact_path,
                hint="Check that the build directory is writable.",
            ),
        )
    return (
        BuildArtifact(path=artifact_path, target="html", artifact_type="document"),
        (),
    )


def write_single_page_script_artifact(
    project_root: Path,
    output_dir: Path,
    filesystem: FileSystem,
) -> tuple[BuildArtifact | None, tuple[Diagnostic, ...]]:
    """Write the JavaScript used by the interactive single-page TOC.

    Args:
        project_root: Absolute project root directory.
        output_dir: Relative output directory (e.g. ``build/html``).
        filesystem: Filesystem service used for writing.

    Returns:
        Script artifact on success, plus any write diagnostics.
    """
    artifact_path = project_root / output_dir / _SCRIPT_OUTPUT_PATH
    try:
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        filesystem.write_text(artifact_path, toc_script())
    except Exception as exc:
        return None, (
            Diagnostic(
                severity="error",
                code="BLD006",
                message=f"Cannot write HTML script artifact: {exc}",
                path=artifact_path,
                hint="Check that the build directory is writable.",
            ),
        )
    return (
        BuildArtifact(path=artifact_path, target="html", artifact_type="script"),
        (),
    )


def write_single_page_support_artifacts(
    project_root: Path,
    html: str,
    output_dir: Path,
    filesystem: FileSystem,
) -> tuple[tuple[BuildArtifact, ...], tuple[Diagnostic, ...]]:
    """Write the document and JavaScript assets for single-page HTML.

    Args:
        project_root: Absolute project root directory.
        html: Complete HTML document content.
        output_dir: Relative output directory (e.g. ``build/html``).
        filesystem: Filesystem service used for writing.

    Returns:
        Produced artifacts plus diagnostics.
    """
    artifact, html_diags = write_single_page_artifact(
        project_root, html, output_dir, filesystem
    )
    if artifact is None:
        return (), html_diags

    script_artifact, script_diags = write_single_page_script_artifact(
        project_root, output_dir, filesystem
    )
    if script_artifact is None:
        return (), (*html_diags, *script_diags)
    return (artifact, script_artifact), (*html_diags, *script_diags)


def _anchor(title: str) -> str:
    """Build an anchor for ."""
    lowered = title.lower()
    stripped = re.sub(r"[^\w\s-]", "", lowered)
    return re.sub(r"\s+", "-", stripped).strip("-")


def _escape(text: str) -> str:
    """Escape ."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _inline(text: str) -> str:
    """Render inline ."""
    text = _IMAGE_RE.sub(
        lambda m: f'<img src="{m.group(2)}" alt="{_escape(m.group(1))}">', text
    )
    text = _LINK_RE.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"`(.+?)`", lambda m: f"<code>{_escape(m.group(1))}</code>", text)
    return text


def _remove_generated_markdown_toc(body_html: str) -> str:
    """Remove generated markdown toc."""
    pattern = re.compile(
        r'\n?<h2 id="table-of-contents">Table of Contents</h2>.*?(?=\n<h2\b|\Z)',
        re.DOTALL,
    )
    return pattern.sub("", body_html, count=1)


__all__ = [
    "build_single_page_html",
    "render_markdown_to_html",
    "write_single_page_artifact",
    "write_single_page_script_artifact",
    "write_single_page_support_artifacts",
]
