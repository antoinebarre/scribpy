"""Interactive table-of-contents hamburger menu widget (REQ-003).

Generates an HTML/CSS/JS snippet that renders a toggleable sidebar
menu listing the document headings with anchor links.
"""

from __future__ import annotations

from scribpy.core.document import Heading

_TOC_CSS = """\
<style>
.scribpy-toc-toggle {
  position: fixed;
  top: 16px;
  left: 16px;
  z-index: 10000;
  background: #333;
  color: #fff;
  border: none;
  font-size: 24px;
  width: 40px;
  height: 40px;
  cursor: pointer;
  border-radius: 4px;
  line-height: 40px;
  text-align: center;
}
.scribpy-toc-toggle:hover {
  background: #555;
}
.scribpy-toc-panel {
  position: fixed;
  top: 0;
  left: -320px;
  width: 300px;
  height: 100%;
  background: #f8f9fa;
  border-right: 1px solid #ddd;
  overflow-y: auto;
  padding: 60px 20px 20px;
  z-index: 9999;
  transition: left 0.3s ease;
  box-shadow: 2px 0 8px rgba(0,0,0,0.1);
}
.scribpy-toc-panel.open {
  left: 0;
}
.scribpy-toc-panel ul {
  list-style: none;
  padding: 0;
  margin: 0;
}
.scribpy-toc-panel li {
  margin: 4px 0;
}
.scribpy-toc-panel a {
  text-decoration: none;
  color: #333;
  display: block;
  padding: 4px 8px;
  border-radius: 4px;
}
.scribpy-toc-panel a:hover {
  background: #e9ecef;
}
</style>
"""

_TOC_JS = """\
<script>
(function() {
  var btn = document.querySelector('.scribpy-toc-toggle');
  var panel = document.querySelector('.scribpy-toc-panel');
  btn.addEventListener('click', function() {
    panel.classList.toggle('open');
  });
})();
</script>
"""


def generate_toc_html(headings: tuple[Heading, ...]) -> str:
    """Generate the TOC widget HTML with CSS and JavaScript.

    Produces a hamburger button and a sliding panel containing an
    unordered list of heading links.  Indentation is based on heading
    level.

    Args:
        headings: Ordered sequence of document headings.

    Returns:
        Complete HTML snippet (CSS + markup + JS) ready for insertion
        into the document ``<body>``.
    """
    lines: list[str] = []
    lines.append(_TOC_CSS)
    lines.append(
        '<button class="scribpy-toc-toggle" '
        'aria-label="Table of contents">&#9776;</button>',
    )
    lines.append('<nav class="scribpy-toc-panel"><ul>')

    for heading in headings:
        indent = (heading.level - 1) * 16
        lines.append(
            f'<li style="padding-left:{indent}px">'
            f'<a href="#{heading.anchor}">{heading.text}</a></li>',
        )

    lines.append("</ul></nav>")
    lines.append(_TOC_JS)
    return "\n".join(lines)
