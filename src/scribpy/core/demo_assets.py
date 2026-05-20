"""Static text assets used by the generated demo project."""

DEMO_CSS = """\
:root {
  color-scheme: light;
  --bg: #f8fafc;
  --surface: #ffffff;
  --surface-soft: #eef2ff;
  --text: #1f2937;
  --muted: #64748b;
  --heading: #0f172a;
  --accent: #2563eb;
  --accent-soft: #dbeafe;
  --border: #cbd5e1;
  --shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  background:
    radial-gradient(
      circle at top left,
      rgba(37, 99, 235, 0.12),
      transparent 28rem
    ),
    var(--bg);
  color: var(--text);
  font-family: Inter, ui-sans-serif, system-ui, sans-serif;
  line-height: 1.7;
  margin: 0;
}
.page-shell {
  display: grid;
  gap: 2rem;
  grid-template-columns: minmax(15rem, 18rem) minmax(0, 72ch);
  justify-content: center;
  padding: 3rem 2rem 4rem;
}
.document-content {
  background: var(--surface);
  border: 1px solid rgba(203, 213, 225, 0.8);
  border-radius: 1.5rem;
  box-shadow: var(--shadow);
  min-width: 0;
  padding: clamp(1.5rem, 3vw, 3rem);
}
.document-content h1,
.document-content h2,
.document-content h3 {
  color: var(--heading);
  line-height: 1.2;
  scroll-margin-top: 1.5rem;
}
.document-content h1 {
  font-size: clamp(2rem, 5vw, 3rem);
  margin-top: 0;
}
.document-content h2 {
  border-top: 1px solid var(--border);
  margin-top: 2.5rem;
  padding-top: 2rem;
}
.document-content img {
  border-radius: 1rem;
  display: block;
  margin: 1.5rem auto;
  max-width: 100%;
}
a { color: var(--accent); }
.toc-panel {
  align-self: start;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(203, 213, 225, 0.9);
  border-radius: 1.25rem;
  box-shadow: var(--shadow);
  padding: 1.25rem;
  position: sticky;
  top: 2rem;
  max-height: calc(100vh - 4rem);
  overflow: hidden;
}
.toc-eyebrow {
  color: var(--muted);
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
}
.toc-list {
  list-style: none;
  margin: 1rem 0 0;
  max-height: calc(100vh - 13rem);
  overflow-y: auto;
  padding: 0;
  scrollbar-width: thin;
}
.toc-list > li { position: relative; }
.toc-list a {
  border-left: 3px solid transparent;
  color: var(--muted);
  display: block;
  padding: 0.3rem 0.5rem;
  text-decoration: none;
}
.toc-list a:hover,
.toc-list a[aria-current="true"] {
  background: var(--accent-soft);
  border-color: var(--accent);
  color: var(--heading);
}
.toc-level-2 { padding-left: 1.6rem; }
.toc-level-3 { padding-left: 0.8rem; }
.toc-children {
  list-style: none;
  margin: 0.35rem 0 0.5rem;
  padding: 0 0 0 0.7rem;
}
.toc-collapse {
  background: transparent;
  border: 0;
  color: var(--muted);
  cursor: pointer;
  height: 1.8rem;
  left: 0;
  padding: 0;
  position: absolute;
  top: 0;
  width: 1.3rem;
}
.toc-collapse::before {
  content: "›";
  display: block;
  font-size: 1.15rem;
  transform: rotate(0deg);
  transition: transform 150ms ease;
}
.toc-collapse[aria-expanded="true"]::before { transform: rotate(90deg); }
.toc-search-label {
  display: block;
  font-size: 0.8rem;
  font-weight: 600;
  margin-bottom: 0.35rem;
}
.toc-search {
  border: 1px solid var(--border);
  border-radius: 999px;
  font: inherit;
  padding: 0.55rem 0.8rem;
  width: 100%;
}
.toc-toggle { display: none; }
@media (max-width: 900px) {
  .page-shell { display: block; padding: 1rem; }
  .toc-toggle { display: inline-flex; margin: 1rem; }
  .toc-panel { display: none; margin: 0 1rem 1rem; position: static; }
  .toc-panel.is-open { display: block; }
}
"""

__all__ = ["DEMO_CSS"]
