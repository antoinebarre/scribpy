"""Construction of Document objects from SourceFile entries.

Functions:
    parse_document_file -- read, parse and extract semantics for one SourceFile.
    parse_documents     -- batch-parse an ordered collection of SourceFile objects.
    order_by_index      -- reorder SourceFile objects to match a DocumentIndex.

Diagnostics emitted:
    PRS001 -- source file is unreadable.
    PRS003 -- Markdown parsing failed unexpectedly.
    PRS004 -- semantic extraction produced an inconsistent result.
"""

from __future__ import annotations

from pathlib import Path

from scribpy.model.diagnostic import Diagnostic
from scribpy.model.document import Document
from scribpy.model.index import DocumentIndex
from scribpy.model.markdown import Heading, MarkdownAst
from scribpy.model.protocols import FileSystem, MarkdownParser
from scribpy.model.results import ParseResult
from scribpy.model.source import SourceFile
from scribpy.parser.extractors import extract_assets, extract_headings, extract_links
from scribpy.parser.frontmatter import parse_frontmatter
from scribpy.parser.markdown import parse_markdown

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_document_file(
    source_file: SourceFile,
    filesystem: FileSystem,
    parser: MarkdownParser | None = None,
) -> tuple[Document | None, tuple[Diagnostic, ...]]:
    """Read and parse a single ``SourceFile`` into a ``Document``.

    The pipeline for a single file is:
        read_text -> parse_frontmatter -> parse_markdown -> extract semantics
        -> build Document

    Failures at any stage are captured as ``Diagnostic`` objects and returned
    alongside a ``None`` document so that callers can continue processing the
    remaining files.

    Args:
        source_file: Source file descriptor carrying the absolute and relative
            paths to the Markdown file.
        filesystem: Injected filesystem service used to read the source text.
        parser: Optional external ``MarkdownParser``. When ``None`` the bundled
            ``markdown-it-py`` adapter is used.

    Returns:
        A ``(Document | None, diagnostics)`` pair. ``Document`` is ``None``
        when a blocking error (PRS001 or PRS003) prevents document construction.
        Frontmatter diagnostics (PRS002) are non-blocking: a document is still
        returned with an empty frontmatter mapping.
    """
    source, read_diagnostics = _read_source(source_file.path, filesystem)
    if source is None:
        return None, read_diagnostics

    fm_result = parse_frontmatter(source, path=source_file.path)
    diagnostics: list[Diagnostic] = list(read_diagnostics) + list(fm_result.diagnostics)

    ast, parse_diagnostics = _parse_body(fm_result.body, source_file.path, parser)
    diagnostics.extend(parse_diagnostics)
    if ast is None:
        return None, tuple(diagnostics)

    headings = extract_headings(ast)
    links = extract_links(ast)
    assets = extract_assets(ast)

    frontmatter = fm_result.frontmatter if not fm_result.diagnostics else {}
    title = _resolve_title(frontmatter, headings)

    document = Document(
        path=source_file.path,
        relative_path=source_file.relative_path,
        source=source,
        frontmatter=frontmatter,
        ast=ast,
        title=title,
        headings=headings,
        links=links,
        assets=assets,
    )
    return document, tuple(diagnostics)


def parse_documents(
    source_files: list[SourceFile],
    filesystem: FileSystem,
    parser: MarkdownParser | None = None,
) -> ParseResult:
    """Parse an ordered collection of ``SourceFile`` objects into a ``ParseResult``.

    The order of ``source_files`` is preserved in the returned
    ``ParseResult.documents`` tuple. Files that fail to parse (PRS001,
    PRS003) are excluded from ``documents`` but their diagnostics are
    included. The overall ``failed`` flag is ``True`` when at least one file
    could not be parsed.

    Args:
        source_files: Ordered list of source files, typically from a
            ``DocumentIndex``.
        filesystem: Injected filesystem service.
        parser: Optional external ``MarkdownParser``.

    Returns:
        A ``ParseResult`` aggregating all documents and diagnostics.
    """
    documents: list[Document] = []
    diagnostics: list[Diagnostic] = []
    failed = False

    for source_file in source_files:
        document, file_diagnostics = parse_document_file(
            source_file, filesystem, parser
        )
        diagnostics.extend(file_diagnostics)
        if document is None:
            failed = True
        else:
            documents.append(document)

    return ParseResult(
        documents=tuple(documents),
        diagnostics=tuple(diagnostics),
        failed=failed,
    )


def order_by_index(
    index: DocumentIndex,
    source_files: tuple[SourceFile, ...],
) -> tuple[list[SourceFile], tuple[Diagnostic, ...]]:
    """Reorder ``source_files`` to match the sequence declared in ``index``.

    Source files are matched by their ``relative_path``. Index entries that
    have no matching source file produce a ``PRS001`` diagnostic and are
    skipped; the returned list only contains files that could be resolved.

    Args:
        index: Document index defining the canonical processing order.
        source_files: Source files discovered by the project scanner.

    Returns:
        A ``(ordered_files, diagnostics)`` pair. ``ordered_files`` contains
        the resolved files in index order. ``diagnostics`` contains one
        ``PRS001`` entry for every index path that could not be matched.
    """
    lookup = {sf.relative_path: sf for sf in source_files}
    ordered: list[SourceFile] = []
    diagnostics: list[Diagnostic] = []

    for path in index.paths:
        sf = lookup.get(path)
        if sf is None:
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="PRS001",
                    message=f"Index entry not found in discovered source files: {path}",
                    path=path,
                    hint="Check that the file exists under the source directory.",
                )
            )
        else:
            ordered.append(sf)

    return ordered, tuple(diagnostics)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _read_source(
    path: Path,
    filesystem: FileSystem,
) -> tuple[str | None, tuple[Diagnostic, ...]]:
    try:
        return filesystem.read_text(path), ()
    except Exception as exc:
        return None, (
            Diagnostic(
                severity="error",
                code="PRS001",
                message=f"Cannot read source file: {exc}",
                path=path,
                hint="Check that the file exists and is readable.",
            ),
        )


def _parse_body(
    body: str,
    path: Path,
    parser: MarkdownParser | None,
) -> tuple[MarkdownAst | None, tuple[Diagnostic, ...]]:
    try:
        return parse_markdown(body, parser=parser), ()
    except Exception as exc:
        return None, (
            Diagnostic(
                severity="error",
                code="PRS003",
                message=f"Markdown parsing failed: {exc}",
                path=path,
                hint="Check that the file contains valid CommonMark Markdown.",
            ),
        )


def _resolve_title(
    frontmatter: dict[str, object],
    headings: tuple[Heading, ...],
) -> str | None:
    if "title" in frontmatter:
        return str(frontmatter["title"])
    for heading in headings:
        if heading.level == 1:
            return heading.title
    return None


__all__ = ["order_by_index", "parse_document_file", "parse_documents"]
