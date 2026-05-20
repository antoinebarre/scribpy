"""Report node dataclasses — containers and leaf elements."""

from __future__ import annotations

from dataclasses import dataclass, field

from .errors import InvalidChildError, InvalidTableError, ReportDepthError

# ---------------------------------------------------------------------------
# Leaf types
# ---------------------------------------------------------------------------

TextStyle = str  # "bold" | "italic" | "code" | "strikethrough" | "plain"


@dataclass
class Text:
    """Inline text with optional formatting.

    Attributes:
        content: The raw text string.
        style: One of ``plain``, ``bold``, ``italic``, ``code``,
            ``strikethrough``.
    """

    content: str
    style: TextStyle = "plain"

    def __post_init__(self) -> None:
        """Validate style value."""
        valid = {"plain", "bold", "italic", "code", "strikethrough"}
        if self.style not in valid:
            raise ValueError(f"Invalid text style '{self.style}'. Choose from {valid}.")


@dataclass
class LineBreak:
    """Hard line break rendered as two trailing spaces followed by a newline.

    Use inside a ``Paragraph`` list to force a line break within a block
    without starting a new paragraph.
    """


@dataclass
class Paragraph:
    """Block of text or a sequence of inline elements.

    Attributes:
        content: A plain string or a list of ``Text`` / ``LineBreak`` nodes.
    """

    content: str | list[Text | LineBreak]

    def __post_init__(self) -> None:
        """Validate that string content is not empty."""
        if isinstance(self.content, str) and not self.content:
            raise ValueError("Paragraph content cannot be empty.")


@dataclass
class CodeBlock:
    """Fenced code block with optional language hint.

    Attributes:
        code: Source code string.
        language: Optional language identifier for syntax highlighting.
    """

    code: str
    language: str = ""


@dataclass
class Table:
    """GFM table with a mandatory header row.

    Attributes:
        headers: Column header labels (must be non-empty).
        rows: Data rows; each row must have the same number of cells
            as ``headers``.
    """

    headers: list[str]
    rows: list[list[str]]

    def __post_init__(self) -> None:
        """Validate headers and row dimensions."""
        if not self.headers:
            raise InvalidTableError("headers list cannot be empty.")
        col_count = len(self.headers)
        for i, row in enumerate(self.rows):
            if len(row) != col_count:
                raise InvalidTableError(
                    f"Row {i} has {len(row)} cells but header has {col_count}."
                )


@dataclass
class BulletList:
    """Unordered list rendered with ``-`` markers.

    Attributes:
        items: Non-empty list of item strings.
    """

    items: list[str]

    def __post_init__(self) -> None:
        """Validate that at least one item is present."""
        if not self.items:
            raise ValueError("BulletList must have at least one item.")


@dataclass
class NumberedList:
    """Ordered list rendered with ``1.`` markers.

    Attributes:
        items: Non-empty list of item strings.
    """

    items: list[str]

    def __post_init__(self) -> None:
        """Validate that at least one item is present."""
        if not self.items:
            raise ValueError("NumberedList must have at least one item.")


@dataclass
class Image:
    """Inline image node that references an existing file.

    Attributes:
        path: Image path or URL.
        alt: Alt text displayed when the image cannot load.
        title: Optional tooltip title.
    """

    path: str
    alt: str = ""
    title: str = ""


@dataclass
class FigureAsset:
    """A figure produced by an asset renderer (e.g. matplotlib chart).

    The renderer is responsible for saving the figure to ``output_path``
    and returning the relative path to embed in the GFM output.

    Attributes:
        renderer: An object implementing the ``AssetRenderer`` protocol.
        output_path: Where the rendered asset file will be written.
        alt: Alt text for the resulting ``Image`` node.
        caption: Optional caption rendered as italic text below the image.
    """

    renderer: object
    output_path: str
    alt: str = ""
    caption: str = ""


@dataclass
class ImageFile:
    """A user-supplied image file to be embedded alongside the report.

    When the report is saved via ``Report.save()``, the file at
    ``source_path`` is copied into an ``assets/`` sub-directory next to the
    output ``.md`` file, and the GFM link is rewritten to the relative copy.

    When the report is rendered to a string via ``Report.render()``, the
    original ``source_path`` is embedded as-is (no copying).

    Attributes:
        source_path: Absolute or relative path to the source image file.
        alt: Alt text for the GFM image tag.
        caption: Optional caption rendered as italic text below the image.
    """

    source_path: str
    alt: str = ""
    caption: str = ""

    def __post_init__(self) -> None:
        """Validate that source_path is not blank."""
        if not self.source_path.strip():
            raise ValueError("ImageFile source_path cannot be empty.")


@dataclass
class HorizontalRule:
    """Horizontal separator rendered as ``---``."""


@dataclass
class BlockQuote:
    """Block quote rendered with ``>`` markers.

    Attributes:
        content: Text content, may contain newlines.
    """

    content: str


# Union of all leaf types
LeafNode = (
    Paragraph
    | Text
    | LineBreak
    | CodeBlock
    | Table
    | BulletList
    | NumberedList
    | Image
    | ImageFile
    | FigureAsset
    | HorizontalRule
    | BlockQuote
)

# ---------------------------------------------------------------------------
# Container types
# ---------------------------------------------------------------------------

_LEAF_TYPES = (
    Paragraph,
    Text,
    LineBreak,
    CodeBlock,
    Table,
    BulletList,
    NumberedList,
    Image,
    ImageFile,
    FigureAsset,
    HorizontalRule,
    BlockQuote,
)

MAX_HEADING_DEPTH = 6
_CHAPTER_HEADING_LEVEL = 1
_SECTION_BASE_LEVEL = 2


@dataclass
class Section:
    """Heading container that maps to H2…H6 based on nesting depth.

    Attributes:
        title: Non-empty section heading text.
        children: Ordered child nodes (sections or leaf elements).
    """

    title: str
    children: list[Section | LeafNode] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate that title is not blank."""
        if not self.title.strip():
            raise ValueError("Section title cannot be empty.")

    def add(self, *items: Section | LeafNode) -> Section:
        """Append one or more children and return self for chaining.

        Args:
            *items: Child nodes to append.

        Returns:
            This Section instance.

        Raises:
            InvalidChildError: If an item is not a valid child type.
        """
        for item in items:
            _validate_section_child(item)
            self.children.append(item)
        return self


def _validate_section_child(child: object) -> None:
    """Raise InvalidChildError if child is not allowed inside a Section.

    Args:
        child: The object being added.

    Raises:
        InvalidChildError: If the child type is not permitted.
    """
    if not isinstance(child, (Section, *_LEAF_TYPES)):
        raise InvalidChildError("Section", type(child).__name__)


@dataclass
class Chapter:
    """Top-level container that maps to H1.

    Attributes:
        title: Non-empty chapter heading text.
        children: Ordered child nodes (sections or leaf elements).
    """

    title: str
    children: list[Section | LeafNode] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate that title is not blank."""
        if not self.title.strip():
            raise ValueError("Chapter title cannot be empty.")

    def add(self, *items: Section | LeafNode) -> Chapter:
        """Append one or more children and return self for chaining.

        Args:
            *items: Child nodes to append.

        Returns:
            This Chapter instance.

        Raises:
            InvalidChildError: If an item is not a valid child type.
        """
        for item in items:
            _validate_chapter_child(item)
            self.children.append(item)
        return self


def _validate_chapter_child(child: object) -> None:
    """Raise InvalidChildError if child is not allowed inside a Chapter.

    Args:
        child: The object being added.

    Raises:
        InvalidChildError: If the child type is not permitted.
    """
    if not isinstance(child, (Section, *_LEAF_TYPES)):
        raise InvalidChildError("Chapter", type(child).__name__)


@dataclass
class Report:
    """Root of the report document.

    Attributes:
        title: Non-empty report title (rendered as H1).
        children: Ordered Chapter nodes.
        toc: When True, a GFM table of contents is prepended.
        auto_numbering: When True, headings are prefixed with section
            numbers (e.g. ``1.``, ``1.1.``).
    """

    title: str
    children: list[Chapter] = field(default_factory=list)
    toc: bool = False
    auto_numbering: bool = False

    def __post_init__(self) -> None:
        """Validate that title is not blank."""
        if not self.title.strip():
            raise ValueError("Report title cannot be empty.")

    def add(self, *items: Chapter) -> Report:
        """Append one or more Chapter nodes and return self for chaining.

        Args:
            *items: Chapter nodes to append.

        Returns:
            This Report instance.

        Raises:
            InvalidChildError: If an item is not a Chapter.
        """
        for item in items:
            if not isinstance(item, Chapter):
                raise InvalidChildError("Report", type(item).__name__)
            self.children.append(item)
        return self

    def render(self) -> str:
        """Render this report to a GFM string.

        Returns:
            A valid GitHub Flavored Markdown document string.
        """
        from .renderer import render_report

        return render_report(self)

    def save(self, path: str) -> None:
        """Render and write this report to a file.

        Args:
            path: Destination file path. Intermediate directories are
                created automatically.
        """
        from .renderer import save_report

        save_report(self, path)


def compute_section_depth(depth_from_chapter: int) -> int:
    """Return the GFM heading level for a Section at the given depth.

    Depth 1 means the Section is a direct child of a Chapter (H2).
    Each additional level of nesting increments the heading number.

    Args:
        depth_from_chapter: Nesting depth relative to its parent
            Chapter (1-based).

    Returns:
        An integer between 2 and 6 representing the ``#`` heading level.

    Raises:
        ReportDepthError: If the resulting level would exceed H6.
    """
    level = _SECTION_BASE_LEVEL + depth_from_chapter - 1
    if level > MAX_HEADING_DEPTH:
        raise ReportDepthError(level)
    return level
