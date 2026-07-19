"""HTML page assembly from body fragment and navigation entries."""

from __future__ import annotations

from html import escape


def build_page(
    body_html: str,
    nav_entries: list[dict[str, str | int]],
    default_css: str,
    user_css: str | None,
    burger_js: str,
) -> str:
    """Assemble a complete, standalone HTML page.

    The page embeds all CSS and JavaScript inline so it is fully portable
    without any external resources.  The burger menu navigation panel is
    built from ``nav_entries`` and does not appear in the document body.

    Args:
        body_html: HTML fragment for the document body (no wrapper tags).
        nav_entries: List of navigation entry dicts, each with keys
            ``"level"`` (int), ``"title"`` (str), and ``"slug"`` (str).
        default_css: CSS source for the base stylesheet.
        user_css: Optional user-supplied CSS appended after the base styles.
        burger_js: JavaScript source for the burger menu behaviour.

    Returns:
        Complete HTML document as a string.
    """
    css_block = default_css
    if user_css:
        css_block = css_block + "\n\n/* ── User styles ── */\n" + user_css

    nav_items_html = _render_nav_items(nav_entries)
    burger_svg_open, burger_svg_close = _burger_icons()

    btn = (
        '<button id="scribpy-burger"'
        ' aria-label="Table des matières"'
        ' aria-expanded="false"'
        ' aria-controls="scribpy-nav">\n'
        f'  <span class="icon-open">{burger_svg_open}</span>\n'
        f'  <span class="icon-close">{burger_svg_close}</span>\n'
        "</button>"
    )

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
{css_block}
</style>
</head>
<body>

{btn}

<div id="scribpy-overlay" aria-hidden="true"></div>

<nav id="scribpy-nav" aria-label="Table des matières">
  <div id="scribpy-nav-header">Table des matières</div>
  <ul id="scribpy-nav-list" role="list">
{nav_items_html}
  </ul>
</nav>

<main>
{body_html}
</main>

<script>
{burger_js}
</script>
</body>
</html>"""


def _render_nav_items(nav_entries: list[dict[str, str | int]]) -> str:
    """Render navigation list items as HTML.

    Args:
        nav_entries: Navigation entries from ``build_nav_entries()``.

    Returns:
        HTML string of ``<li>`` elements, indented for readability.
    """
    lines: list[str] = []
    for entry in nav_entries:
        level = int(entry["level"])
        title = escape(str(entry["title"]))
        slug = escape(str(entry["slug"]))
        lines.append(
            f'    <li><a href="#{slug}" class="depth-{level}">{title}</a></li>'
        )
    return "\n".join(lines)


def _burger_icons() -> tuple[str, str]:
    """Return SVG icon markup for the open and close burger states.

    Returns:
        Tuple of (open_svg, close_svg) HTML strings.
    """
    _svg_attrs = (
        'width="20" height="20" viewBox="0 0 20 20" fill="none" '
        'xmlns="http://www.w3.org/2000/svg" aria-hidden="true"'
    )
    open_svg = (
        f"<svg {_svg_attrs}>"
        '<rect x="3" y="5" width="14" height="2" rx="1" fill="white"/>'
        '<rect x="3" y="9" width="14" height="2" rx="1" fill="white"/>'
        '<rect x="3" y="13" width="14" height="2" rx="1" fill="white"/>'
        "</svg>"
    )
    _line_attrs = 'stroke="white" stroke-width="2" stroke-linecap="round"'
    close_svg = (
        f"<svg {_svg_attrs}>"
        f'<line x1="5" y1="5" x2="15" y2="15" {_line_attrs}/>'
        f'<line x1="15" y1="5" x2="5" y2="15" {_line_attrs}/>'
        "</svg>"
    )
    return open_svg, close_svg
