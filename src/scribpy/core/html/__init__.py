"""HTML export for assembled Markdown documents."""

from __future__ import annotations

import importlib.resources
from pathlib import Path

from scribpy.core.html import converter, page_builder, toc_extractor

_ASSETS = importlib.resources.files("scribpy.core.html.assets")


def html_export(
    source: Path,
    output: Path,
    toc_depth: int = 3,
    css: Path | None = None,
) -> None:
    """Export an assembled Markdown file to a standalone HTML page.

    The TOC Markdown block is removed from the document body and its
    headings are used to build a burger menu navigation panel embedded
    in the HTML.  All CSS and JavaScript are inlined so the output file
    is fully self-contained.

    Args:
        source: Path to the assembled ``.md`` file produced by
            ``concatenate()``.
        output: Destination path for the generated ``.html`` file.
            Parent directories must already exist.
        toc_depth: Maximum heading depth to include in the burger menu,
            relative to H1.  Matches ``build.toc_depth`` from the manifest
            (1 = H2 only, 2 = H2+H3, 3 = H2+H3+H4).  Defaults to 3.
        css: Optional path to a user CSS file.  Its contents are appended
            after the built-in base stylesheet, allowing full override.

    Raises:
        FileNotFoundError: If ``source`` or ``css`` (when provided) does
            not exist.
        UnicodeDecodeError: If ``source`` or ``css`` is not valid UTF-8.
    """
    content = source.read_text(encoding="utf-8")

    headings = toc_extractor.extract_headings(content, toc_depth)
    stripped = toc_extractor.strip_toc_block(content)
    nav_entries = toc_extractor.build_nav_entries(headings)

    body_html = converter.to_html(stripped)

    default_css = _read_asset("default.css")
    burger_js = _read_asset("burger.js")

    user_css: str | None = None
    if css is not None:
        user_css = css.read_text(encoding="utf-8")

    html = page_builder.build_page(
        body_html, nav_entries, default_css, user_css, burger_js
    )
    output.write_text(html, encoding="utf-8")


def _read_asset(name: str) -> str:
    """Read a bundled asset file as UTF-8 text.

    Args:
        name: Asset filename relative to the ``assets/`` package directory.

    Returns:
        Asset file contents as a string.
    """
    return (_ASSETS / name).read_text(encoding="utf-8")


__all__ = ["html_export"]
