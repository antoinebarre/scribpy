"""Random GitHub-flavored Markdown generator with Lorem Ipsum content."""

import random
from collections.abc import Callable
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MarkdownConfig:
    """Controls which optional sections appear in the generated document.

    Attributes:
        include_math: Emit the LaTeX math section.
        include_mermaid: Emit the Mermaid diagram section.
        include_alerts: Emit the GitHub Alerts section.
        include_footnotes: Emit footnote body and end-of-document definitions.
        include_details: Emit the collapsible HTML ``<details>`` section.
        section_separator: Markdown divider inserted between every section.
    """

    include_math: bool = True
    include_mermaid: bool = True
    include_alerts: bool = True
    include_footnotes: bool = True
    include_details: bool = True
    section_separator: str = "\n\n---\n\n"


_DEFAULT_CONFIG = MarkdownConfig()


# ---------------------------------------------------------------------------
# Corpus
# ---------------------------------------------------------------------------

_WORDS: tuple[str, ...] = (
    "lorem",
    "ipsum",
    "dolor",
    "sit",
    "amet",
    "consectetur",
    "adipiscing",
    "elit",
    "sed",
    "do",
    "eiusmod",
    "tempor",
    "incididunt",
    "ut",
    "labore",
    "et",
    "dolore",
    "magna",
    "aliqua",
    "enim",
    "ad",
    "minim",
    "veniam",
    "quis",
    "nostrud",
    "exercitation",
    "ullamco",
    "laboris",
    "nisi",
    "aliquip",
    "ex",
    "ea",
    "commodo",
    "consequat",
    "duis",
    "aute",
    "irure",
    "reprehenderit",
    "in",
    "voluptate",
    "velit",
    "esse",
    "cillum",
    "fugiat",
    "nulla",
    "pariatur",
    "excepteur",
    "sint",
    "occaecat",
    "cupidatat",
    "non",
    "proident",
    "sunt",
    "culpa",
    "qui",
    "officia",
    "deserunt",
    "mollit",
    "anim",
    "id",
    "est",
    "laborum",
)

_CODE_SNIPPETS: tuple[tuple[str, str], ...] = (
    ("python", 'def greet(name: str) -> str:\n    return f"Hello, {name}!"'),
    ("javascript", "const greet = (name) => `Hello, ${name}!`;"),
    ("bash", '#!/bin/bash\necho "Hello, World!"'),
    (
        "typescript",
        "function greet(name: string): string {\n  return `Hello, ${name}`;\n}",
    ),
    ("sql", "SELECT id, name FROM users\nWHERE active = TRUE\nORDER BY name;"),
    ("yaml", "name: lorem\nversion: 1.0.0\ndescription: ipsum dolor sit amet"),
    ("json", '{\n  "name": "lorem",\n  "version": "1.0.0",\n  "active": true\n}'),
    ("rust", 'fn main() {\n    println!("Hello, world!");\n}'),
    ("go", 'func main() {\n\tfmt.Println("Hello, world!")\n}'),
    ("css", "body {\n  font-family: sans-serif;\n  color: #333;\n}"),
)

_EMOJIS: tuple[str, ...] = (
    ":rocket:",
    ":star:",
    ":fire:",
    ":tada:",
    ":zap:",
    ":book:",
    ":gear:",
    ":bulb:",
    ":warning:",
    ":white_check_mark:",
    ":x:",
    ":memo:",
    ":mag:",
    ":heart:",
    ":thumbsup:",
    ":eyes:",
    ":sparkles:",
    ":construction:",
)

_ALERT_TYPES: tuple[str, ...] = ("NOTE", "TIP", "IMPORTANT", "WARNING", "CAUTION")

_MATH_INLINE_EXPRS: tuple[str, ...] = (
    r"E = mc^2",
    r"a^2 + b^2 = c^2",
    r"\pi \approx 3.14159",
    r"e^{i\pi} + 1 = 0",
    r"\hbar = h / 2\pi",
)

_MATH_BLOCK_EXPRS: tuple[str, ...] = (
    r"\sum_{i=1}^{n} i = \frac{n(n+1)}{2}",
    r"\int_0^\infty e^{-x^2}\, dx = \frac{\sqrt{\pi}}{2}",
    r"\frac{d}{dx}\!\left(x^n\right) = nx^{n-1}",
    r"\nabla \cdot \mathbf{E} = \frac{\rho}{\varepsilon_0}",
    r"\mathbf{F} = m\mathbf{a}",
)

_MERMAID_DIAGRAMS: tuple[str, ...] = (
    (
        "graph TD\n"
        "    A[Start] --> B{Decision?}\n"
        "    B -->|Yes| C[Process]\n"
        "    B -->|No| D[End]\n"
        "    C --> D"
    ),
    (
        "sequenceDiagram\n"
        "    Alice->>Bob: Hello Bob!\n"
        "    Bob-->>Alice: Hi Alice!\n"
        "    Alice->>Bob: How are you?\n"
        "    Bob-->>Alice: Fine, thanks!"
    ),
    (
        "pie title Lorem Distribution\n"
        '    "Ipsum" : 42\n'
        '    "Dolor" : 28\n'
        '    "Amet" : 30'
    ),
    (
        "flowchart LR\n"
        "    A[Input] --> B[Parse]\n"
        "    B --> C[Transform]\n"
        "    C --> D[Export]"
    ),
    (
        "classDiagram\n"
        "    Animal <|-- Duck\n"
        "    Animal <|-- Fish\n"
        "    Animal : +String name\n"
        "    Animal: +speak() str"
    ),
)

_USERNAMES: tuple[str, ...] = ("alice", "bob", "charlie", "dave", "eve", "mallory")

_EXAMPLE_URLS: tuple[str, ...] = (
    "https://example.com",
    "https://example.com/docs/getting-started",
    "https://example.com/api/reference",
    "https://example.com/guide/quickstart",
)

_PLACEHOLDER_IMAGE_URLS: tuple[str, ...] = (
    "https://placehold.co/600x400",
    "https://placehold.co/800x300",
    "https://placehold.co/400x400",
    "https://placehold.co/1200x600",
)

_TABLE_ALIGNMENTS: tuple[tuple[str, ...], ...] = (
    (":---", "---", "---:"),
    (":---:", ":---:", ":---:"),
    (":---", ":---", ":---"),
    ("---:", "---:", "---:"),
)

_STATUS_VALUES: tuple[str, ...] = (
    "Active",
    "Pending",
    "Done",
    "Cancelled",
    "In Progress",
)


# ---------------------------------------------------------------------------
# Primitive text helpers
# ---------------------------------------------------------------------------


def _words(rng: random.Random, n: int) -> str:
    """Picks n random Lorem Ipsum words and returns them space-joined.

    Args:
        rng: Seeded random instance used for all draws.
        n: Number of words to pick (with replacement).

    Returns:
        A single string of n lowercase words separated by spaces.
    """
    return " ".join(rng.choices(_WORDS, k=n))


def _sentence(rng: random.Random) -> str:
    """Returns a capitalised Lorem Ipsum sentence of 6–14 random words.

    Args:
        rng: Seeded random instance used for word selection and length.

    Returns:
        A sentence string starting with an uppercase letter and ending with '.'.
    """
    raw = _words(rng, rng.randint(6, 14))
    return raw[0].upper() + raw[1:] + "."


def _paragraph(rng: random.Random) -> str:
    """Returns 3–5 Lorem Ipsum sentences joined into a single paragraph.

    Args:
        rng: Seeded random instance forwarded to each ``_sentence`` call.

    Returns:
        A multi-sentence paragraph string (no trailing newline).
    """
    sentences = [_sentence(rng) for _ in range(rng.randint(3, 5))]
    return " ".join(sentences)


# ---------------------------------------------------------------------------
# Markdown element builders (pure, deterministic)
# ---------------------------------------------------------------------------


def _heading(level: int, text: str) -> str:
    """Returns a GFM heading line for the given level (1–6).

    Args:
        level: Heading depth — 1 renders as ``# ``, 6 as ``###### ``.
        text: Heading label (not escaped).

    Returns:
        A string like ``## My Title``.
    """
    return f"{'#' * level} {text}"


def _bold(text: str) -> str:
    """Wraps text in ``**`` markers for GFM bold.

    Args:
        text: Content to emphasise.

    Returns:
        ``**text**``
    """
    return f"**{text}**"


def _italic(text: str) -> str:
    """Wraps text in ``*`` markers for GFM italic.

    Args:
        text: Content to emphasise.

    Returns:
        ``*text*``
    """
    return f"*{text}*"


def _bold_italic(text: str) -> str:
    """Wraps text in ``***`` markers for GFM bold-italic.

    Args:
        text: Content to emphasise.

    Returns:
        ``***text***``
    """
    return f"***{text}***"


def _strikethrough(text: str) -> str:
    """Wraps text in ``~~`` markers for GFM strikethrough.

    Args:
        text: Content to strike through.

    Returns:
        ``~~text~~``
    """
    return f"~~{text}~~"


def _subscript(text: str) -> str:
    """Wraps text in ``~`` markers for GFM subscript (GitHub extension).

    Args:
        text: Content to render as subscript (e.g. ``'2'`` for H₂O).

    Returns:
        ``~text~``
    """
    return f"~{text}~"


def _superscript(text: str) -> str:
    """Wraps text in ``^`` markers for GFM superscript (GitHub extension).

    Args:
        text: Content to render as superscript (e.g. ``'2'`` for x²).

    Returns:
        ``^text^``
    """
    return f"^{text}^"


def _inline_code(text: str) -> str:
    """Wraps text in single-backtick markers for GFM inline code.

    Args:
        text: Code fragment to display verbatim.

    Returns:
        `` `text` ``
    """
    return f"`{text}`"


def _link(text: str, url: str) -> str:
    """Returns a GFM inline hyperlink.

    Args:
        text: Visible link label.
        url: Link destination.

    Returns:
        ``[text](url)``
    """
    return f"[{text}]({url})"


def _image(alt: str, url: str) -> str:
    """Returns a GFM image embed.

    Args:
        alt: Alternative text shown when the image cannot be displayed.
        url: Image source URL.

    Returns:
        ``![alt](url)``
    """
    return f"![{alt}]({url})"


def _autolink(url: str) -> str:
    """Wraps a URL in angle-bracket autolink syntax so GFM renders it as a link.

    Args:
        url: Absolute URL to autolink.

    Returns:
        ``<url>``
    """
    return f"<{url}>"


def _blockquote(text: str) -> str:
    """Prefixes every line of text with ``> `` to form a GFM blockquote.

    Multiline strings produce multi-line blockquotes; nesting is achieved by
    passing already-quoted text (each inner ``>`` gains another ``> `` prefix).

    Args:
        text: Raw content to quote (may contain newlines).

    Returns:
        A string where every line starts with ``> ``.
    """
    return "\n".join(f"> {line}" for line in text.splitlines())


def _code_block(lang: str, code: str) -> str:
    """Returns a fenced code block with the given language identifier.

    Args:
        lang: Language hint for syntax highlighting (e.g. ``'python'``).
        code: Source code body (no trailing newline required).

    Returns:
        A triple-backtick fenced block string.
    """
    return f"```{lang}\n{code}\n```"


def _table_row(cells: list[str]) -> str:
    """Formats a list of cell strings as a single GFM pipe-table row.

    Args:
        cells: Cell contents (not escaped); order determines column position.

    Returns:
        A string like ``| cell1 | cell2 | cell3 |``.
    """
    return "| " + " | ".join(cells) + " |"


def _table(headers: list[str], rows: list[list[str]], aligns: list[str]) -> str:
    """Assembles a full GFM pipe table from headers, alignment markers, and data rows.

    Args:
        headers: Column header strings.
        rows: Data rows — each inner list must have the same length as headers.
        aligns: Per-column GFM alignment markers (e.g. ``:---``, ``---:``, ``:---:``).

    Returns:
        A multi-line table string including the header and separator rows.
    """
    lines = [_table_row(headers), _table_row(aligns)]
    lines.extend(_table_row(row) for row in rows)
    return "\n".join(lines)


def _task_item(done: bool, text: str) -> str:
    """Returns a single GFM task-list item.

    Args:
        done: When True the checkbox is ticked (``[x]``), otherwise empty (``[ ]``).
        text: Item label.

    Returns:
        ``- [x] text`` or ``- [ ] text``.
    """
    return f"- [{'x' if done else ' '}] {text}"


def _alert(kind: str, text: str) -> str:
    """Returns a GitHub-flavored alert block.

    GitHub renders these blockquotes with a coloured icon based on ``kind``.

    Args:
        kind: One of ``NOTE``, ``TIP``, ``IMPORTANT``, ``WARNING``, ``CAUTION``.
        text: Alert body (single line).

    Returns:
        A two-line string ``> [!KIND]\\n> text``.
    """
    return f"> [!{kind}]\n> {text}"


def _footnote_ref(idx: int) -> str:
    """Returns an inline footnote reference marker.

    Args:
        idx: Positive integer identifying the footnote.

    Returns:
        ``[^idx]`` — place this inline in body text.
    """
    return f"[^{idx}]"


def _footnote_def(idx: int, note: str) -> str:
    """Returns a footnote definition line to be placed at the end of the document.

    Args:
        idx: Must match the corresponding ``_footnote_ref`` index.
        note: Expanded footnote text.

    Returns:
        ``[^idx]: note``
    """
    return f"[^{idx}]: {note}"


def _math_inline(expr: str) -> str:
    """Wraps a LaTeX expression in single-dollar inline math delimiters.

    Args:
        expr: LaTeX source (without delimiters).

    Returns:
        ``$expr$``
    """
    return f"${expr}$"


def _math_block(expr: str) -> str:
    """Wraps a LaTeX expression in double-dollar display-math delimiters.

    Args:
        expr: LaTeX source (without delimiters).

    Returns:
        A three-line string ``$$\\nexpr\\n$$``.
    """
    return f"$$\n{expr}\n$$"


def _details(summary: str, content: str) -> str:
    """Returns an HTML ``<details>`` collapsible block rendered by GitHub.

    Args:
        summary: Clickable label shown when the block is collapsed.
        content: Body shown when the block is expanded; may contain Markdown.

    Returns:
        A multi-line HTML string with ``<details>``, ``<summary>``, and body.
    """
    return f"<details>\n<summary>{summary}</summary>\n\n{content}\n\n</details>"


def _mermaid(diagram: str) -> str:
    """Returns a fenced ``mermaid`` code block containing the diagram source.

    GitHub renders these blocks as SVG diagrams.

    Args:
        diagram: Raw Mermaid diagram source (without fence markers).

    Returns:
        A triple-backtick fenced block tagged ``mermaid``.
    """
    return _code_block("mermaid", diagram)


def _mention(username: str) -> str:
    """Returns a GitHub @mention string.

    Args:
        username: GitHub handle (without the ``@`` prefix).

    Returns:
        ``@username``
    """
    return f"@{username}"


def _issue_ref(n: int) -> str:
    """Returns a GitHub issue/PR reference string (e.g. ``#42``).

    Args:
        n: Issue or pull-request number.

    Returns:
        ``#n``
    """
    return f"#{n}"


def _horizontal_rule() -> str:
    """Returns a GFM horizontal rule (thematic break).

    Returns:
        ``---``
    """
    return "---"


# ---------------------------------------------------------------------------
# Compound list builders
# ---------------------------------------------------------------------------


def _unordered_list(rng: random.Random) -> str:
    """Builds a 3-item unordered list with 2 sub-items and 1 sub-sub-item.

    Args:
        rng: Seeded random instance for Lorem Ipsum content.

    Returns:
        A newline-joined string of dash-prefixed list items at three indent levels.
    """
    items = [f"- {_sentence(rng)}" for _ in range(3)]
    items += [f"  - {_sentence(rng)}", f"  - {_sentence(rng)}"]
    items.append(f"    - {_sentence(rng)}")
    return "\n".join(items)


def _ordered_list(rng: random.Random) -> str:
    """Builds a 3-item numbered list with 2 nested sub-items.

    Args:
        rng: Seeded random instance for Lorem Ipsum content.

    Returns:
        A newline-joined string of numbered list items with one level of nesting.
    """
    items = [f"{i}. {_sentence(rng)}" for i in range(1, 4)]
    items += [f"   1. {_sentence(rng)}", f"   2. {_sentence(rng)}"]
    return "\n".join(items)


def _task_list(rng: random.Random) -> str:
    """Builds a 6-item GFM task list with randomly ticked checkboxes.

    Args:
        rng: Seeded random instance for checkbox state and Lorem Ipsum content.

    Returns:
        A newline-joined string of ``- [ ]`` / ``- [x]`` items.
    """
    items = [_task_item(rng.choice([True, False]), _sentence(rng)) for _ in range(6)]
    return "\n".join(items)


def _random_table(rng: random.Random) -> str:
    """Builds a 5-row GFM table (Name / Status / Description) with a random
    column alignment.

    Args:
        rng: Seeded random instance for alignment choice and cell content.

    Returns:
        A multi-line GFM pipe-table string.
    """
    headers = ["Name", "Status", "Description"]
    aligns = list(rng.choice(_TABLE_ALIGNMENTS))
    rows = [
        [
            _words(rng, 1).title(),
            rng.choice(_STATUS_VALUES),
            _words(rng, rng.randint(2, 4)),
        ]
        for _ in range(5)
    ]
    return _table(headers, rows, aligns)


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------


def _section_title(rng: random.Random) -> str:
    """Generates the H1 title block: emoji heading, subtitle blockquote,
    author @mention, and semver badge.

    Args:
        rng: Seeded random instance for title words, emoji, username and
            version numbers.

    Returns:
        A multi-line string forming the document header (no trailing blank line).
    """
    title = _words(rng, rng.randint(3, 6)).title()
    emoji = rng.choice(_EMOJIS)
    author = _mention(rng.choice(_USERNAMES))
    version = f"{rng.randint(1, 5)}.{rng.randint(0, 9)}.{rng.randint(0, 9)}"
    lines = [
        _heading(1, f"{emoji} {title}"),
        "",
        f"> {_sentence(rng)}",
        "",
        (
            f"{_bold('Author:')} {author} &nbsp; "
            f"{_bold('Version:')} {version} &nbsp; "
            f"{_bold('Status:')} Active"
        ),
    ]
    return "\n".join(lines)


def _section_headings(rng: random.Random) -> str:
    """Demonstrates all six heading levels (H1–H6), each followed by a
    Lorem Ipsum sentence.

    Args:
        rng: Seeded random instance for heading titles and sentence content.

    Returns:
        A section string opening with an H2 ``## Heading Levels`` label.
    """
    lines: list[str] = [_heading(2, "Heading Levels")]
    for level in range(1, 7):
        title = _words(rng, rng.randint(3, 5)).title()
        lines.append(_heading(level, title))
        lines.append(_sentence(rng))
    return "\n\n".join(lines)


def _section_emphasis(rng: random.Random) -> str:
    """Shows all inline-emphasis variants: bold, italic, bold-italic,
    strikethrough, sub/superscript, and inline code.

    Args:
        rng: Seeded random instance for Lorem Ipsum word selection.

    Returns:
        A section string under ``## Text Formatting``.
    """
    lines = [
        _heading(2, "Text Formatting"),
        (
            f"Regular text with {_bold(_words(rng, 3))}, "
            f"{_italic(_words(rng, 3))}, and {_bold_italic(_words(rng, 3))}."
        ),
        (
            f"Strikethrough: {_strikethrough(_words(rng, 3))}. "
            f"Subscript: H{_subscript('2')}O. "
            f"Superscript: x{_superscript('2')}."
        ),
        (
            f"Inline code: {_inline_code('print(hello)')} and "
            f"{_inline_code('from pathlib import Path')}."
        ),
        _paragraph(rng),
    ]
    return "\n\n".join(lines)


def _section_lists(rng: random.Random) -> str:
    """Groups the unordered, ordered, and task lists under a single
    ``## Lists`` section.

    Args:
        rng: Seeded random instance forwarded to each list builder.

    Returns:
        A section string containing three H3 sub-sections.
    """
    parts = [
        _heading(2, "Lists"),
        _heading(3, "Unordered List"),
        _unordered_list(rng),
        _heading(3, "Ordered List"),
        _ordered_list(rng),
        _heading(3, "Task List"),
        _task_list(rng),
    ]
    return "\n\n".join(parts)


def _section_code(rng: random.Random) -> str:
    """Shows two randomly selected fenced code blocks with inline-code
    examples in the preamble.

    Args:
        rng: Seeded random instance for snippet selection.

    Returns:
        A section string under ``## Code`` with two H3 language sub-sections.
    """
    lang1, code1 = rng.choice(_CODE_SNIPPETS)
    lang2, code2 = rng.choice(_CODE_SNIPPETS)
    parts = [
        _heading(2, "Code"),
        (
            f"Use {_inline_code('import os')} for system calls or "
            f"{_inline_code('from pathlib import Path')} for file paths."
        ),
        _heading(3, f"{lang1.title()} Example"),
        _code_block(lang1, code1),
        _heading(3, f"{lang2.title()} Example"),
        _code_block(lang2, code2),
    ]
    return "\n\n".join(parts)


def _section_links_images(rng: random.Random) -> str:
    """Demonstrates inline links, autolinks, reference-style links, and an
    embedded image with caption.

    Args:
        rng: Seeded random instance for URL and alt-text selection.

    Returns:
        A section string under ``## Links & Images``.
    """
    url = rng.choice(_EXAMPLE_URLS)
    img_url = rng.choice(_PLACEHOLDER_IMAGE_URLS)
    alt = _words(rng, 3).title()
    parts = [
        _heading(2, "Links & Images"),
        f"Visit {_link('the documentation', url)} for details.",
        f"Autolink: {_autolink('https://example.com')}.",
        f"Reference: see {_link('this guide', rng.choice(_EXAMPLE_URLS))} for more.",
        _image(alt, img_url),
        f"*Figure 1: {_sentence(rng)}*",
    ]
    return "\n\n".join(parts)


def _section_tables(rng: random.Random) -> str:
    """Renders a randomly aligned GFM table preceded by a Lorem Ipsum paragraph.

    Args:
        rng: Seeded random instance forwarded to ``_random_table`` and ``_paragraph``.

    Returns:
        A section string under ``## Tables``.
    """
    parts = [
        _heading(2, "Tables"),
        _paragraph(rng),
        _random_table(rng),
    ]
    return "\n\n".join(parts)


def _section_blockquotes(rng: random.Random) -> str:
    """Produces a simple blockquote followed by a two-level nested blockquote example.

    Args:
        rng: Seeded random instance for Lorem Ipsum sentence content.

    Returns:
        A section string under ``## Blockquotes`` with an H3 nested-blockquote demo.
    """
    nested_inner = _blockquote(_sentence(rng))
    nested_outer = _blockquote(f"{_sentence(rng)}\n>\n{nested_inner}")
    parts = [
        _heading(2, "Blockquotes"),
        _blockquote(_paragraph(rng)),
        _heading(3, "Nested Blockquote"),
        nested_outer,
    ]
    return "\n\n".join(parts)


def _section_alerts(rng: random.Random) -> str:
    """Emits all five GitHub Alert types (NOTE, TIP, IMPORTANT, WARNING, CAUTION).

    Args:
        rng: Seeded random instance for alert body sentences.

    Returns:
        A section string under ``## Alerts (GitHub-flavored)``.
    """
    alerts = [_alert(kind, _sentence(rng)) for kind in _ALERT_TYPES]
    parts = [_heading(2, "Alerts (GitHub-flavored)"), *alerts]
    return "\n\n".join(parts)


def _section_footnotes(rng: random.Random) -> tuple[str, list[str]]:
    """Builds the footnotes section body and the matching definition lines.

    The definitions must be appended at the very end of the document (after all
    other sections) for GitHub to render them correctly.

    Args:
        rng: Seeded random instance for footnote body sentences.

    Returns:
        A 2-tuple ``(section_body, definitions)`` where ``section_body`` is the
        paragraph with inline ``[^n]`` references and ``definitions`` is a list of
        ``[^n]: text`` strings to join and append at document end.
    """
    refs = [_footnote_ref(i) for i in range(1, 4)]
    defs = [_footnote_def(i, _sentence(rng)) for i in range(1, 4)]
    text = (
        f"This section contains footnotes{refs[0]}. "
        f"Each reference{refs[1]} expands below the document. "
        f"Definitions are collected at the end{refs[2]}."
    )
    section = "\n\n".join([_heading(2, "Footnotes"), text])
    return section, defs


def _section_math(rng: random.Random) -> str:
    """Shows one inline LaTeX formula and one display-math block from the corpus.

    Args:
        rng: Seeded random instance for expression selection and Lorem Ipsum filler.

    Returns:
        A section string under ``## Mathematics`` with an H3 block-equation sub-section.
    """
    expr_inline = rng.choice(_MATH_INLINE_EXPRS)
    expr_block = rng.choice(_MATH_BLOCK_EXPRS)
    parts = [
        _heading(2, "Mathematics"),
        f"The formula {_math_inline(expr_inline)} is well known in {_words(rng, 3)}.",
        _heading(3, "Block Equation"),
        _math_block(expr_block),
    ]
    return "\n\n".join(parts)


def _section_mermaid(rng: random.Random) -> str:
    """Embeds one randomly selected Mermaid diagram preceded by a Lorem Ipsum paragraph.

    Args:
        rng: Seeded random instance for diagram and paragraph selection.

    Returns:
        A section string under ``## Diagrams (Mermaid)``.
    """
    parts = [
        _heading(2, "Diagrams (Mermaid)"),
        _paragraph(rng),
        _mermaid(rng.choice(_MERMAID_DIAGRAMS)),
    ]
    return "\n\n".join(parts)


def _section_details(rng: random.Random) -> str:
    """Creates two ``<details>`` collapsible blocks: one with a code
    snippet, one with plain text.

    Args:
        rng: Seeded random instance for summary labels, snippet selection
            and paragraph content.

    Returns:
        A section string under ``## Collapsible Sections``.
    """
    summary = _words(rng, rng.randint(3, 5)).title()
    lang, code = rng.choice(_CODE_SNIPPETS)
    content = f"{_paragraph(rng)}\n\n{_code_block(lang, code)}"
    parts = [
        _heading(2, "Collapsible Sections"),
        _paragraph(rng),
        _details(summary, content),
        _details(_words(rng, 3).title(), _paragraph(rng)),
    ]
    return "\n\n".join(parts)


def _section_misc(rng: random.Random) -> str:
    """Groups GitHub-specific extras: emojis, @mentions, #refs, HR, hard
    line break, HTML comment, kbd, and mark.

    Args:
        rng: Seeded random instance for emoji sampling, username/issue
            selection and Lorem Ipsum filler.

    Returns:
        A section string under ``## Miscellaneous`` containing multiple H3 sub-sections.
    """
    emojis = " ".join(rng.sample(list(_EMOJIS), k=6))
    user = _mention(rng.choice(_USERNAMES))
    issue = _issue_ref(rng.randint(1, 999))
    parts = [
        _heading(2, "Miscellaneous"),
        _heading(3, "Emojis"),
        emojis,
        _heading(3, "Mentions & Issue References"),
        f"Reviewed by {user}. Related to {issue}. {_sentence(rng)}",
        _heading(3, "Horizontal Rule"),
        _sentence(rng),
        _horizontal_rule(),
        _sentence(rng),
        _heading(3, "Hard Line Break"),
        f"{_sentence(rng)}  \n{_sentence(rng)}",
        _heading(3, "HTML Comment"),
        "<!-- This comment is invisible in rendered output -->",
        _heading(3, "Keyboard Keys"),
        (
            f"Press {_inline_code('Ctrl')} + {_inline_code('Shift')} + "
            f"{_inline_code('P')} to open the palette."
        ),
        _heading(3, "Highlighted Text"),
        f"Use <mark>{_words(rng, 3)}</mark> to highlight important content.",
    ]
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Assembly helpers
# ---------------------------------------------------------------------------

_OPTIONAL_SECTION_FNS: tuple[tuple[str, Callable[[random.Random], str]], ...] = (
    ("include_alerts", _section_alerts),
    ("include_math", _section_math),
    ("include_mermaid", _section_mermaid),
    ("include_details", _section_details),
)


def _core_sections(rng: random.Random) -> list[str]:
    """Returns the eight mandatory sections always present regardless of config.

    Args:
        rng: Seeded random instance forwarded to each section builder.

    Returns:
        Ordered list of section strings (title → headings → … → blockquotes).
    """
    return [
        _section_title(rng),
        _section_headings(rng),
        _section_emphasis(rng),
        _section_lists(rng),
        _section_code(rng),
        _section_links_images(rng),
        _section_tables(rng),
        _section_blockquotes(rng),
    ]


def _optional_sections(rng: random.Random, config: MarkdownConfig) -> list[str]:
    """Returns optional section strings whose flag in *config* is True,
    in document order.

    Args:
        rng: Seeded random instance forwarded to each enabled section builder.
        config: Resolved ``MarkdownConfig`` controlling which sections to include.

    Returns:
        List of enabled section strings (alerts → math → mermaid → details).
    """
    return [fn(rng) for attr, fn in _OPTIONAL_SECTION_FNS if getattr(config, attr)]


def _footnote_parts(rng: random.Random, include: bool) -> tuple[list[str], list[str]]:
    """Generates footnote section and definition lines, or returns empty
    lists when disabled.

    Args:
        rng: Seeded random instance for footnote content.
        include: When False both returned lists are empty and rng is not advanced.

    Returns:
        A 2-tuple ``([section_body], [def_line, …])`` or ``([], [])``
            when include is False.
    """
    if not include:
        return [], []
    section, defs = _section_footnotes(rng)
    return [section], defs


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_markdown(
    seed: int | None = None,
    config: MarkdownConfig | None = None,
) -> str:
    """Generates a random Markdown document covering all GitHub-flavored features.

    The output exercises headings (H1–H6), emphasis (bold, italic, strikethrough,
    subscript, superscript), ordered/unordered/task lists, fenced code blocks,
    inline code, links, images, tables, blockquotes, GitHub Alerts, footnotes,
    LaTeX math, Mermaid diagrams, collapsible ``<details>`` blocks, emojis,
    @mentions, issue references, horizontal rules, and HTML elements.

    Mandatory sections (always present): title, headings, emphasis, lists, code,
    links & images, tables, blockquotes, miscellaneous.

    Optional sections (controlled by ``config``): alerts, math, mermaid, details,
    footnotes.

    Args:
        seed: Optional integer seed for reproducible output. When ``None`` the
            output differs on every call.
        config: Optional ``MarkdownConfig`` controlling optional sections and the
            section separator. Defaults to ``MarkdownConfig()`` (all sections on).

    Returns:
        A complete UTF-8 Markdown string ready to be written to a ``.md`` file.
    """
    resolved = config if config is not None else _DEFAULT_CONFIG
    rng = random.Random(seed)
    footnote_sections, footnote_defs = _footnote_parts(rng, resolved.include_footnotes)
    tail = ["\n".join(footnote_defs)] if footnote_defs else []
    parts = (
        _core_sections(rng)
        + _optional_sections(rng, resolved)
        + footnote_sections
        + [_section_misc(rng)]
        + tail
    )
    return resolved.section_separator.join(parts)
