"""scribpy — Parse, transform, and export Markdown documents.

Submodules
----------
scribpy.utils
    File-system helpers: discover, read, and write ``.md`` files.
scribpy.parsers
    Markdown ingestion and tokenisation.
scribpy.core
    Document model and abstract syntax tree.
scribpy.editors
    In-place mutation helpers for the document model.
scribpy.exporters
    Renderers targeting PDF, HTML, DOCX, and other formats.
scribpy.plugins
    Extension points for hooking into the pipeline.

Typical usage
-------------
::

    from scribpy.utils import list_md_files, read_md_file

    for path in list_md_files("./docs"):
        content = read_md_file(path)
        ...
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__: str = version("scribpy")
except PackageNotFoundError:
    __version__ = "0.0.0.dev0"

__all__ = ["__version__"]
