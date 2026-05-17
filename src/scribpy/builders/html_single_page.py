"""Single-page HTML builder."""

from __future__ import annotations

import re
from pathlib import Path

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
  <style>{_toc_styles()}</style>
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
        filesystem.write_text(artifact_path, _toc_script())
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


def _toc_styles() -> str:
    """Return the inline CSS that drives the TOC panel and hamburger.

    These styles are injected directly into the <head> so they remain active
    regardless of which user-supplied CSS file is loaded.  User stylesheets can
    still override individual rules via specificity; they simply cannot remove
    the TOC panel entirely by accident.
    """
    return """
  /* ── TOC shell layout ──────────────────────────────────────────────── */
  .page-shell {
    box-sizing: border-box;
    display: grid;
    grid-template-columns: minmax(14rem, 18rem) 1fr;
    gap: 0;
    min-height: 100vh;
    width: 100%;
  }
  .toc-panel {
    align-self: start;
    background: rgba(255,255,255,.88);
    border-right: 1px solid rgba(203,213,225,.9);
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    max-height: 100vh;
    overflow: visible;
    padding: 1.25rem;
    position: sticky;
    top: 0;
    width: 100%;
  }
  .document-content {
    box-sizing: border-box;
    min-width: 0;
    padding: clamp(1.5rem, 3vw, 3rem);
    width: 100%;
  }

  /* ── TOC internals ──────────────────────────────────────────────────── */
  .toc-eyebrow {
    font-size: .75rem;
    font-weight: 700;
    letter-spacing: .08em;
    margin: 0 0 .75rem;
    text-transform: uppercase;
  }
  .toc-search-label {
    display: block;
    font-size: .8rem;
    font-weight: 600;
    margin-bottom: .35rem;
  }
  .toc-search {
    border: 1px solid #cbd5e1;
    border-radius: 999px;
    font: inherit;
    padding: .45rem .75rem;
    width: 100%;
    box-sizing: border-box;
  }
  .toc-list {
    list-style: none;
    margin: .75rem 0 0;
    max-height: calc(100vh - 11rem);
    overflow-y: auto;
    padding: 0;
    scrollbar-width: thin;
  }
  .toc-list li + li { margin-top: .25rem; }
  .toc-list > li { position: relative; }
  .toc-list a {
    border-left: 3px solid transparent;
    color: #64748b;
    display: block;
    font-size: .88rem;
    padding: .28rem .5rem;
    text-decoration: none;
    transition: background-color 120ms, border-color 120ms, color 120ms;
  }
  .toc-list a:hover,
  .toc-list a[aria-current="true"] {
    background: #dbeafe;
    border-color: #2563eb;
    color: #0f172a;
  }
  .toc-list a[aria-current="location"] {
    border-color: #93c5fd;
    color: #1d4ed8;
  }
  .toc-level-2 { padding-left: .8rem; }
  .toc-level-3 { padding-left: 1.6rem; }
  .toc-children {
    list-style: none;
    margin: .25rem 0 .4rem;
    padding: 0 0 0 .5rem;
  }
  .toc-collapse {
    background: transparent;
    border: 0;
    color: #64748b;
    cursor: pointer;
    height: 1.7rem;
    left: 0;
    padding: 0;
    position: absolute;
    top: 0;
    width: 1.2rem;
  }
  .toc-collapse::before {
    content: "›";
    display: block;
    font-size: 1.1rem;
    transform: rotate(0deg);
    transition: transform 150ms ease;
  }
  .toc-collapse[aria-expanded="true"]::before { transform: rotate(90deg); }

  /* ── Hamburger button — always visible, fixed top-left ─────────────── */
  .toc-toggle {
    align-items: center;
    background: #0f172a;
    border: 0;
    border-radius: .5rem;
    cursor: pointer;
    display: flex;
    justify-content: center;
    left: .75rem;
    line-height: 0;
    padding: .5rem .55rem;
    position: fixed;
    top: .75rem;
    z-index: 300;
  }
  /* Three-bar icon — pure CSS, no SVG */
  .toc-hamburger {
    background: #fff;
    border-radius: 2px;
    display: block;
    height: .15rem;
    position: relative;
    transition: background 200ms;
    width: 1.25rem;
  }
  .toc-hamburger::before,
  .toc-hamburger::after {
    background: #fff;
    border-radius: 2px;
    content: "";
    display: block;
    height: .15rem;
    left: 0;
    position: absolute;
    transition: transform 200ms, top 200ms;
    width: 1.25rem;
  }
  .toc-hamburger::before { top: -.42rem; }
  .toc-hamburger::after  { top:  .42rem; }
  /* Morphs into × when panel is open */
  .toc-toggle[aria-expanded="true"] .toc-hamburger { background: transparent; }
  .toc-toggle[aria-expanded="true"] .toc-hamburger::before {
    top: 0; transform: rotate(45deg);
  }
  .toc-toggle[aria-expanded="true"] .toc-hamburger::after {
    top: 0; transform: rotate(-45deg);
  }

  /* ── Desktop: panel open by default, shifts content right ───────────── */
  .page-shell {
    transition: grid-template-columns 220ms ease;
  }
  .page-shell.toc-collapsed {
    grid-template-columns: 0 1fr;
  }
  .toc-panel {
    transition: opacity 220ms ease, transform 220ms ease;
  }
  .page-shell.toc-collapsed .toc-panel {
    opacity: 0;
    pointer-events: none;
    transform: translateX(-100%);
  }
  /* Offset content so hamburger never overlaps text */
  .document-content { padding-left: 3.5rem; }

  /* ── Mobile: panel hidden by default, slides in as overlay ──────────── */
  @media (max-width: 900px) {
    .page-shell {
      display: block;
      padding-top: 3rem;
    }
    .document-content { padding-left: clamp(1.5rem, 3vw, 3rem); }
    .toc-panel {
      box-shadow: 4px 0 24px rgba(15,23,42,.18);
      display: none;
      height: 100%;
      left: 0;
      max-height: 100vh;
      overflow-y: auto;
      padding-top: 4rem;
      position: fixed;
      top: 0;
      width: min(20rem, 90vw);
      z-index: 200;
    }
    .toc-panel.is-open { display: flex; }
    /* On mobile the collapsed class is unused — remove transition artefacts */
    .page-shell.toc-collapsed .toc-panel {
      opacity: 1;
      transform: none;
    }
    .toc-list { max-height: none; }
  }
"""


def _toc_script() -> str:
    """Return the TOC script."""
    return """\
(() => {
  const toc = document.querySelector("#page-toc");
  const content = document.querySelector(".document-content");
  const panel = document.querySelector(".toc-panel");
  const toggle = document.querySelector(".toc-toggle");
  const search = document.querySelector("#toc-search");
  if (!toc || !content || !panel || !toggle || !search) return;

  // Skip H1 (document title) — include H2 and H3 only.
  const headings = [...content.querySelectorAll("h2, h3")].filter((h) => h.id);
  if (headings.length === 0) {
    panel.hidden = true;
    toggle.hidden = true;
    return;
  }

  function makeCollapseButton(label) {
    const btn = document.createElement("button");
    btn.className = "toc-collapse";
    btn.type = "button";
    btn.setAttribute("aria-expanded", "false");
    btn.setAttribute("aria-label", `Expand ${label}`);
    return btn;
  }

  function setGroupOpen(children, open) {
    children.hidden = !open;
    const btn = children.parentElement?.querySelector(":scope > .toc-collapse");
    if (btn) btn.setAttribute("aria-expanded", String(open));
  }

  const list = document.createElement("ol");
  list.className = "toc-list";
  let currentH2Item = null;

  headings.forEach((heading) => {
    const item = document.createElement("li");
    const level = parseInt(heading.tagName.slice(1), 10);
    item.className = `toc-level-${level}`;
    item.dataset.headingId = heading.id;

    const link = document.createElement("a");
    link.href = `#${heading.id}`;
    link.textContent = heading.textContent ?? "";

    if (heading.tagName === "H2") {
      const btn = makeCollapseButton(link.textContent);
      const children = document.createElement("ol");
      children.className = "toc-children";
      children.hidden = true;
      btn.addEventListener("click", () => {
        const open = btn.getAttribute("aria-expanded") !== "true";
        setGroupOpen(children, open);
      });
      item.append(btn, link, children);
      currentH2Item = item;
      list.append(item);
      return;
    }

    // H3: nest inside the nearest H2's children list, or fall back to root.
    item.append(link);
    if (heading.tagName === "H3" && currentH2Item) {
      const children = currentH2Item.querySelector(":scope > .toc-children");
      if (children) {
        children.append(item);
        return;
      }
    }
    list.append(item);
  });

  toc.replaceChildren(list);

  // --- Search filter ---
  search.addEventListener("input", () => {
    const query = search.value.trim().toLowerCase();
    if (query.length === 0) {
      list.querySelectorAll("li").forEach((li) => { li.hidden = false; });
      list.querySelectorAll(".toc-children").forEach((c) => setGroupOpen(c, false));
      return;
    }
    // Show/hide leaf items first.
    list.querySelectorAll("li").forEach((li) => {
      const link = li.querySelector(":scope > a");
      li.hidden = !link?.textContent?.toLowerCase().includes(query);
    });
    // Open H2 groups that have at least one visible H3 child.
    list.querySelectorAll(".toc-children").forEach((children) => {
      const anyVisible = [...children.children].some((c) => !c.hidden);
      setGroupOpen(children, anyVisible);
      // Also un-hide the H2 parent if it has visible children.
      if (anyVisible && children.parentElement) {
        children.parentElement.hidden = false;
      }
    });
  });

  // --- Panel toggle: desktop collapses into rail, mobile slides in as overlay ---
  const shell = document.querySelector(".page-shell");
  const isMobile = () => window.matchMedia("(max-width: 900px)").matches;

  // Desktop starts with panel open (aria-expanded = true).
  // Mobile starts with panel closed (aria-expanded = false).
  function initToggle() {
    if (isMobile()) {
      toggle.setAttribute("aria-expanded", "false");
      panel.classList.remove("is-open");
      shell?.classList.remove("toc-collapsed");
    } else {
      toggle.setAttribute("aria-expanded", "true");
      shell?.classList.remove("toc-collapsed");
    }
  }
  initToggle();
  window.matchMedia("(max-width: 900px)").addEventListener("change", initToggle);

  toggle.addEventListener("click", () => {
    if (isMobile()) {
      const open = panel.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(open));
    } else {
      const collapsed = shell?.classList.toggle("toc-collapsed");
      toggle.setAttribute("aria-expanded", String(!collapsed));
    }
  });

  // --- Scroll-spy with ancestor highlight ---
  const linksById = new Map(
    [...toc.querySelectorAll("a[href^='#']")].map((a) => [
      decodeURIComponent(a.getAttribute("href").slice(1)),
      a,
    ])
  );

  function activateLink(id) {
    toc.querySelectorAll("a[aria-current]").forEach((a) => a.removeAttribute("aria-current"));
    const active = linksById.get(id);
    if (!active) return;
    active.setAttribute("aria-current", "true");
    // Highlight ancestor H2 link when an H3 is active.
    const item = active.closest("li");
    const childrenList = item?.parentElement;
    if (childrenList?.classList.contains("toc-children")) {
      setGroupOpen(childrenList, true);
      const parentLink = childrenList.parentElement?.querySelector(":scope > a");
      parentLink?.setAttribute("aria-current", "location");
    }
    // Scroll active link into view within the TOC panel.
    active.scrollIntoView({ block: "nearest" });
  }

  let activeId = null;
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) activeId = entry.target.id;
      });
      if (activeId) activateLink(activeId);
    },
    { rootMargin: "-10% 0px -60% 0px", threshold: 0 }
  );
  headings.forEach((h) => observer.observe(h));
})();
"""


__all__ = [
    "build_single_page_html",
    "render_markdown_to_html",
    "write_single_page_artifact",
    "write_single_page_script_artifact",
    "write_single_page_support_artifacts",
]
