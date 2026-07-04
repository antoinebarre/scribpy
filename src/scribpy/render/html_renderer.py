"""Single-page HTML renderer (REQ-001, REQ-002, REQ-003, REQ-007).

Converts a :class:`ParsedDocument` into a self-contained HTML file,
optionally embedding user CSS and an interactive TOC widget.
Copies referenced images and diagram SVGs to the output directory.
"""

from __future__ import annotations

import logging
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from scribpy.config import CssConfig, TocConfig
from scribpy.core.document import Heading, ParsedDocument
from scribpy.render.toc_widget import generate_toc_html

_log = logging.getLogger(__name__)

_HIGHLIGHT_JS_CDN = (
    "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0"
)

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="{hljs_cdn}/styles/github.min.css">
{css_block}
</head>
<body>
{toc_block}
<main>
{body}
</main>
<script src="{hljs_cdn}/highlight.min.js"></script>
<script>hljs.highlightAll();</script>
</body>
</html>
"""


def _build_css_block(css: CssConfig, output_dir: Path) -> str:
    """Build the ``<style>`` or ``<link>`` element for user CSS.

    If a CSS path is configured, the file is copied to *output_dir*
    and a ``<link>`` tag is emitted.  Otherwise returns an empty
    string.

    Args:
        css: CSS configuration.
        output_dir: Target directory for assets.

    Returns:
        HTML string for the ``<head>`` section.
    """
    if css.path is None:
        return ""
    if not css.path.is_file():
        _log.warning("CSS file not found: %s", css.path)
        return ""

    dest = output_dir / css.path.name
    shutil.copy2(css.path, dest)
    _log.debug("Copied CSS to %s", dest)
    return f'<link rel="stylesheet" href="{css.path.name}">'


def _extract_title(doc: ParsedDocument) -> str:
    """Extract the document title from the first heading.

    Args:
        doc: The parsed document.

    Returns:
        The first heading text, or ``"Untitled"`` if no headings.
    """
    if doc.headings:
        return doc.headings[0].text
    return "Untitled"


def _inject_heading_ids(
    html: str,
    headings: tuple[Heading, ...],
) -> str:
    """Add ``id`` attributes to heading tags for anchor navigation.

    Replaces each ``<hN>`` tag with ``<hN id="anchor">`` using the
    anchors from the parsed headings, matched in document order.

    Args:
        html: The rendered HTML body.
        headings: Ordered headings with their computed anchors.

    Returns:
        HTML with ``id`` attributes injected into heading tags.
    """
    heading_iter = iter(headings)
    pattern = re.compile(r"<(h[1-6])>")

    def _replacer(match: re.Match[str]) -> str:
        heading = next(heading_iter, None)
        if heading is None:
            return match.group(0)
        return f'<{match.group(1)} id="{heading.anchor}">'

    return pattern.sub(_replacer, html)


def _inject_diagram_svgs(
    html: str,
    diagrams_svg: dict[int, str],
) -> str:
    """Replace diagram code block HTML with rendered SVG content.

    The markdown-it renderer produces ``<code>`` blocks for fenced
    code.  This function replaces them with the SVG output.

    Args:
        html: The rendered HTML body.
        diagrams_svg: Mapping from diagram index to SVG markup.

    Returns:
        HTML with diagram code blocks replaced by SVG.
    """
    pattern = re.compile(
        r'<pre><code class="language-(?:plantuml|mermaid)">'
        r".*?</code></pre>",
        re.DOTALL,
    )
    matches = list(pattern.finditer(html))

    for match_idx in reversed(range(len(matches))):
        if match_idx not in diagrams_svg:
            continue
        svg = diagrams_svg[match_idx]
        scoped_svg = _scope_svg(svg, match_idx)
        svg_wrapped = f'<div class="scribpy-diagram">{scoped_svg}</div>'
        start, end = matches[match_idx].span()
        html = html[:start] + svg_wrapped + html[end:]

    return html


def _scope_svg(svg: str, index: int) -> str:
    """Make SVG IDs unique to avoid conflicts between diagrams.

    Replaces generic ``id="mermaid-svg"`` and similar with
    index-scoped variants.

    Args:
        svg: Raw SVG markup from the renderer.
        index: Diagram index for scoping.

    Returns:
        SVG with unique IDs.
    """
    scoped = svg.replace(
        'id="mermaid-svg"',
        f'id="scribpy-diagram-{index}"',
    )
    return scoped.replace(
        "#mermaid-svg",
        f"#scribpy-diagram-{index}",
    )


def _copy_source_assets(source_dir: Path, output_dir: Path) -> None:
    """Copy all files from source_dir into output_dir/source/.

    Places every input file under a ``source/`` sub-directory so the
    original assets are clearly separated from the generated ``index.html``
    and its supporting files.

    Args:
        source_dir: Root directory containing the source assets.
        output_dir: Destination root; files land under ``output_dir/source/``.
    """
    dest_root = output_dir / "source"
    for src_path in source_dir.rglob("*"):
        if not src_path.is_file():
            continue
        rel = src_path.relative_to(source_dir)
        dest_path = dest_root / rel
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dest_path)
        _log.debug("Copied source asset: %s -> %s", src_path, dest_path)


@dataclass(frozen=True)
class HtmlRenderOptions:
    """Options for HTML rendering.

    Attributes:
        source_dir: Base directory for resolving relative image paths.
        css: CSS configuration.
        toc: TOC configuration.
        diagrams_svg: Mapping from diagram index to SVG markup.
    """

    source_dir: Path = field(default_factory=Path.cwd)
    css: CssConfig = field(default_factory=CssConfig)
    toc: TocConfig = field(default_factory=TocConfig)
    diagrams_svg: dict[int, str] = field(default_factory=dict)


def render_html(  # noqa: PLR0913
    doc: ParsedDocument,
    output_dir: Path,
    *,
    source_dir: Path | None = None,
    css: CssConfig | None = None,
    toc: TocConfig | None = None,
    diagrams_svg: dict[int, str] | None = None,
) -> Path:
    """Render a ParsedDocument to a self-contained HTML file.

    Creates the output directory if needed, copies images and CSS,
    injects diagram SVGs, and writes the final ``index.html``.

    Args:
        doc: The parsed document to render.
        output_dir: Directory where output artefacts are written.
        source_dir: Base directory for resolving relative image paths.
            Defaults to the current working directory.
        css: CSS configuration.  Defaults to no custom CSS.
        toc: TOC configuration.  Defaults to disabled.
        diagrams_svg: Mapping from diagram index to SVG markup.

    Returns:
        Path to the generated ``index.html`` file.
    """
    source_dir = source_dir or Path.cwd()
    css = css or CssConfig()
    toc = toc or TocConfig()
    diagrams_svg = diagrams_svg or {}

    output_dir.mkdir(parents=True, exist_ok=True)

    css_block = _build_css_block(css, output_dir)
    toc_block = generate_toc_html(doc.headings) if toc.enabled else ""
    title = _extract_title(doc)

    body = _inject_heading_ids(doc.html, doc.headings)
    if diagrams_svg:
        body = _inject_diagram_svgs(body, diagrams_svg)

    html_content = _HTML_TEMPLATE.format(
        title=title,
        css_block=css_block,
        toc_block=toc_block,
        body=body,
        hljs_cdn=_HIGHLIGHT_JS_CDN,
    )

    output_file = output_dir / "index.html"
    output_file.write_text(html_content, encoding="utf-8")
    _log.info("Written: %s", output_file)

    _copy_source_assets(source_dir, output_dir)

    return output_file
