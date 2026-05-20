"""Pure GFM rendering functions for report nodes."""

from __future__ import annotations

from pathlib import Path

from .nodes import (
    BlockQuote,
    BulletList,
    Chapter,
    CodeBlock,
    FigureAsset,
    HorizontalRule,
    Image,
    ImageFile,
    LineBreak,
    Metadata,
    NumberedList,
    Paragraph,
    Report,
    Section,
    Table,
    Text,
    compute_section_depth,
)
from .numbering import NumberingContext, numbered_title
from .toc import generate_toc


def render_report(report: Report) -> str:
    """Render a Report to a GFM string without copying any assets.

    ``ImageFile`` nodes embed ``source_path`` as-is. To produce a
    self-contained output directory with all images copied, use
    ``save_report`` instead.

    Args:
        report: The root Report node to render.

    Returns:
        A valid GitHub Flavored Markdown document string.
    """
    return _render_report_inner(report, assets_dir=None)


def save_report(report: Report, path: str) -> None:
    """Render report, copy user images, and write the ``.md`` file.

    All ``ImageFile`` nodes are copied into an ``assets/`` sub-directory
    next to ``path``, and the GFM links are rewritten to the relative copies.

    Args:
        report: The root Report node to render.
        path: Destination ``.md`` file path. Intermediate directories are
            created automatically.
    """
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    assets_dir = output.parent / "assets"
    content = _render_report_inner(report, assets_dir=assets_dir)
    output.write_text(content, encoding="utf-8")


def _render_report_inner(report: Report, assets_dir: Path | None) -> str:
    """Core rendering logic shared by ``render_report`` and ``save_report``.

    Args:
        report: The root Report node to render.
        assets_dir: When provided, ``ImageFile`` nodes are copied here and
            embedded with a relative path. When ``None``, ``source_path``
            is embedded as-is.

    Returns:
        A valid GitHub Flavored Markdown document string.
    """
    parts: list[str] = []

    if report.metadata is not None:
        parts.append(_render_frontmatter(report.metadata))

    parts.append(f"# {report.title}")

    if report.toc:
        toc_block = generate_toc(report)
        if toc_block:
            parts.append(toc_block)

    num_ctx = NumberingContext() if report.auto_numbering else None

    if num_ctx is not None:
        num_ctx.push()

    for chapter in report.children:
        parts.append(_render_chapter(chapter, num_ctx, assets_dir))

    if num_ctx is not None:
        num_ctx.pop()

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Chapter
# ---------------------------------------------------------------------------


def _render_chapter(
    chapter: Chapter,
    num_ctx: NumberingContext | None,
    assets_dir: Path | None,
) -> str:
    """Render a Chapter node as a H1 GFM heading with its children.

    Args:
        chapter: The Chapter node to render.
        num_ctx: Active numbering context, or None.
        assets_dir: Target assets directory for ``ImageFile`` copying,
            or None when rendering to a plain string.

    Returns:
        A GFM string for the chapter and all its children.
    """
    title = chapter.title
    if num_ctx is not None:
        num_ctx.next()
        title = numbered_title(chapter.title, num_ctx)

    parts: list[str] = [f"# {title}"]

    if num_ctx is not None:
        num_ctx.push()

    for child in chapter.children:
        parts.append(
            _render_child(
                child, depth=1, num_ctx=num_ctx, assets_dir=assets_dir
            )
        )

    if num_ctx is not None:
        num_ctx.pop()

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Section (recursive)
# ---------------------------------------------------------------------------


def _render_section(
    section: Section,
    depth: int,
    num_ctx: NumberingContext | None,
    assets_dir: Path | None,
) -> str:
    """Render a Section node as a H2–H6 GFM heading with its children.

    Args:
        section: The Section node to render.
        depth: Nesting depth relative to the parent Chapter (1-based).
        num_ctx: Active numbering context, or None.
        assets_dir: Target assets directory for ``ImageFile`` copying,
            or None when rendering to a plain string.

    Returns:
        A GFM string for the section and all its children.
    """
    level = compute_section_depth(depth)
    hashes = "#" * level
    title = section.title

    if num_ctx is not None:
        num_ctx.next()
        title = numbered_title(section.title, num_ctx)

    parts: list[str] = [f"{hashes} {title}"]

    if num_ctx is not None:
        num_ctx.push()

    for child in section.children:
        parts.append(
            _render_child(
                child, depth=depth + 1, num_ctx=num_ctx, assets_dir=assets_dir
            )
        )

    if num_ctx is not None:
        num_ctx.pop()

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Dispatch split into two functions to stay within complexity limit
# ---------------------------------------------------------------------------


def _render_child(
    child: object,
    depth: int,
    num_ctx: NumberingContext | None,
    assets_dir: Path | None,
) -> str:
    """Dispatch a child node to its renderer.

    Args:
        child: Any valid report node.
        depth: Current heading depth (used for Section rendering).
        num_ctx: Active numbering context, or None.
        assets_dir: Target assets directory for ``ImageFile`` copying,
            or None when rendering to a plain string.

    Returns:
        The GFM string for this node.
    """
    if isinstance(child, Section):
        return _render_section(child, depth, num_ctx, assets_dir)
    result = _render_block_leaf(child)
    if result is not None:
        return result
    result = _render_inline_leaf(child, assets_dir)
    if result is not None:
        return result
    raise TypeError(f"Unknown node type: {type(child).__name__}")


def _render_block_leaf(child: object) -> str | None:
    """Render block-level leaf nodes.

    Args:
        child: A candidate leaf node.

    Returns:
        Rendered GFM string, or None if child is not a block leaf.
    """
    if isinstance(child, Paragraph):
        return _render_paragraph(child)
    if isinstance(child, CodeBlock):
        return _render_code_block(child)
    if isinstance(child, Table):
        return _render_table(child)
    if isinstance(child, BulletList):
        return _render_bullet_list(child)
    if isinstance(child, NumberedList):
        return _render_numbered_list(child)
    return None


def _render_inline_leaf(child: object, assets_dir: Path | None) -> str | None:
    """Render inline or simple block leaf nodes.

    Media nodes (``Image``, ``ImageFile``, ``FigureAsset``) are delegated
    to ``_render_media_leaf`` to keep return-statement count within limits.

    Args:
        child: A candidate leaf node.
        assets_dir: Target assets directory for ``ImageFile`` copying,
            or None when rendering to a plain string.

    Returns:
        Rendered GFM string, or None if child is not handled here.
    """
    if isinstance(child, Text):
        return _render_text(child)
    if isinstance(child, HorizontalRule):
        return "---"
    if isinstance(child, BlockQuote):
        return _render_block_quote(child)
    return _render_media_leaf(child, assets_dir)


def _render_media_leaf(child: object, assets_dir: Path | None) -> str | None:
    """Render media leaf nodes: Image, ImageFile, FigureAsset.

    Args:
        child: A candidate leaf node.
        assets_dir: Target assets directory for ``ImageFile`` copying,
            or None when rendering to a plain string.

    Returns:
        Rendered GFM string, or None if child is not a media leaf.
    """
    if isinstance(child, Image):
        return _render_image(child)
    if isinstance(child, ImageFile):
        return _render_image_file(child, assets_dir)
    if isinstance(child, FigureAsset):
        return _render_figure_asset(child)
    return None


# ---------------------------------------------------------------------------
# Leaf renderers
# ---------------------------------------------------------------------------


def _render_paragraph(node: Paragraph) -> str:
    """Render a Paragraph to a plain or inline-formatted GFM string.

    Args:
        node: The Paragraph node to render.

    Returns:
        A GFM string for the paragraph content. ``LineBreak`` nodes inside
        a list produce GFM hard line breaks (two trailing spaces + newline).
    """
    if isinstance(node.content, str):
        return node.content
    return "".join(_render_inline_element(item) for item in node.content)


def _render_inline_element(item: Text | LineBreak) -> str:
    """Render a single inline element within a Paragraph.

    Args:
        item: A ``Text`` or ``LineBreak`` inline node.

    Returns:
        The GFM inline string for this element.
    """
    if isinstance(item, LineBreak):
        return "  \n"
    return _render_text(item)


def _render_text(node: Text) -> str:
    """Render a Text node with GFM inline formatting.

    Args:
        node: The Text node to render.

    Returns:
        A GFM inline string (e.g. ``**bold**``, ``*italic*``).
    """
    match node.style:
        case "bold":
            return f"**{node.content}**"
        case "italic":
            return f"*{node.content}*"
        case "code":
            return f"`{node.content}`"
        case "strikethrough":
            return f"~~{node.content}~~"
        case _:
            return node.content


def _render_code_block(node: CodeBlock) -> str:
    """Render a CodeBlock as a GFM fenced code block.

    Args:
        node: The CodeBlock node to render.

    Returns:
        A triple-backtick fenced block with optional language hint.
    """
    fence = f"```{node.language}" if node.language else "```"
    return f"{fence}\n{node.code}\n```"


def _render_table(node: Table) -> str:
    """Render a Table as a GFM pipe table.

    Args:
        node: The Table node to render.

    Returns:
        A GFM table string with header, separator, and data rows.
    """
    header_row = "| " + " | ".join(node.headers) + " |"
    separator = "| " + " | ".join("---" for _ in node.headers) + " |"
    data_rows = [
        "| " + " | ".join(cell for cell in row) + " |" for row in node.rows
    ]
    return "\n".join([header_row, separator, *data_rows])


def _render_bullet_list(node: BulletList) -> str:
    """Render a BulletList as GFM unordered list items.

    Args:
        node: The BulletList node to render.

    Returns:
        Each item prefixed with ``- ``, joined by newlines.
    """
    return "\n".join(f"- {item}" for item in node.items)


def _render_numbered_list(node: NumberedList) -> str:
    """Render a NumberedList as GFM ordered list items.

    Args:
        node: The NumberedList node to render.

    Returns:
        Each item prefixed with its 1-based index, joined by newlines.
    """
    return "\n".join(f"{i + 1}. {item}" for i, item in enumerate(node.items))


def _render_image(node: Image) -> str:
    """Render an Image node as a GFM inline image.

    Args:
        node: The Image node to render.

    Returns:
        A GFM ``![alt](path)`` or ``![alt](path "title")`` string.
    """
    title_part = f' "{node.title}"' if node.title else ""
    return f"![{node.alt}]({node.path}{title_part})"


def _render_image_file(node: ImageFile, assets_dir: Path | None) -> str:
    """Render an ImageFile node, copying the source file if saving to disk.

    When ``assets_dir`` is provided the source image is copied into it and
    the GFM link uses the relative ``assets/<filename>`` path.  When
    ``assets_dir`` is ``None`` (plain string render) the original
    ``source_path`` is embedded as-is.

    Args:
        node: The ImageFile node to render.
        assets_dir: Target assets directory, or None.

    Returns:
        A GFM image tag, optionally followed by an italic caption.
    """
    if assets_dir is not None:
        from .assets import copy_image_file

        embed_path = copy_image_file(node.source_path, assets_dir)
    else:
        embed_path = node.source_path
    img = f"![{node.alt}]({embed_path})"
    if node.caption:
        return f"{img}\n\n*{node.caption}*"
    return img


def _render_figure_asset(node: FigureAsset) -> str:
    """Render a FigureAsset by invoking its renderer then embedding the result.

    Args:
        node: The FigureAsset node to render.

    Returns:
        A GFM image tag, optionally followed by an italic caption.
    """
    from .assets import AssetRenderer

    assert isinstance(node.renderer, AssetRenderer), (
        f"FigureAsset.renderer must implement AssetRenderer, got {type(node.renderer)}"
    )
    embedded_path = node.renderer.render(node.output_path)
    img = f"![{node.alt}]({embedded_path})"
    if node.caption:
        return f"{img}\n\n*{node.caption}*"
    return img


def _render_block_quote(node: BlockQuote) -> str:
    """Render a BlockQuote node to GFM ``>`` syntax.

    Args:
        node: The BlockQuote node to render.

    Returns:
        Each line of the content prefixed with ``> ``.
    """
    lines = node.content.splitlines()
    return "\n".join(f"> {line}" for line in lines)


def _render_frontmatter(meta: Metadata) -> str:
    """Render a Metadata node as a YAML frontmatter block.

    Only fields with a non-``None`` value are included. The block is
    delimited by ``---`` fences as expected by most Markdown processors
    and the scribpy parser.

    Args:
        meta: The Metadata node to render.

    Returns:
        A ``---``-delimited YAML frontmatter string.
    """
    lines: list[str] = ["---"]
    _add_scalar(lines, "title", meta.title)
    _add_author(lines, meta.author)
    _add_scalar(lines, "date", meta.date)
    _add_scalar(lines, "version", meta.version)
    _add_scalar(lines, "description", meta.description)
    _add_tags(lines, meta.tags)
    for key, value in meta.extra.items():
        _add_scalar(lines, key, str(value))
    lines.append("---")
    return "\n".join(lines)


def _add_scalar(lines: list[str], key: str, value: str | None) -> None:
    """Append a ``key: value`` YAML line if value is not None.

    Args:
        lines: Accumulator list.
        key: YAML key name.
        value: Scalar value, or None to skip.
    """
    if value is not None:
        lines.append(f"{key}: {value}")


def _add_author(lines: list[str], author: str | list[str] | None) -> None:
    """Append author field in scalar or YAML list form.

    Args:
        lines: Accumulator list.
        author: A single author string, a list of authors, or None.
    """
    if author is None:
        return
    if isinstance(author, list):
        lines.append("author:")
        for name in author:
            lines.append(f"  - {name}")
    else:
        lines.append(f"author: {author}")


def _add_tags(lines: list[str], tags: list[str] | None) -> None:
    """Append a YAML list of tags if tags is not None or empty.

    Args:
        lines: Accumulator list.
        tags: List of tag strings, or None.
    """
    if not tags:
        return
    lines.append("tags:")
    for tag in tags:
        lines.append(f"  - {tag}")
