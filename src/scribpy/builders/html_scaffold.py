"""HTML5 document scaffold builder."""

from __future__ import annotations

import re

from scribpy.builders.html_inline_renderer import escape_html
from scribpy.builders.html_single_page_assets import toc_styles


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
  <title>{escape_html(title)}</title>{prefix}{link_tags}
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


def _remove_generated_markdown_toc(body_html: str) -> str:
    """Strip the auto-generated Markdown TOC heading from rendered HTML."""
    pattern = re.compile(
        r'\n?<h2 id="table-of-contents">Table of Contents</h2>'
        r".*?(?=\n<h2\b|\Z)",
        re.DOTALL,
    )
    return pattern.sub("", body_html, count=1)


__all__ = ["build_single_page_html"]
