"""Scribpy logging infrastructure.

Provides a context manager that configures the ``"scribpy"`` logger
hierarchy for the duration of a ``with`` block.  On exit the added
handlers are removed so the caller's logging setup is not polluted.

Typical usage::

    import scribpy

    with scribpy.logging_context(level="INFO"):
        result = scribpy.build_html(...)

    # With a log file:
    with scribpy.logging_context(level="DEBUG", file=Path("build.log")):
        result = scribpy.build_pdf(...)

Sub-modules obtain their own child logger via
``logging.getLogger(__name__)`` and benefit from the configuration
automatically through the ``"scribpy"`` hierarchy.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

_LOGGER_NAME = "scribpy"

_DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _parse_level(level: str | int) -> int:
    """Convert a level name or integer to a numeric logging level.

    Args:
        level: Logging level as a string (e.g. ``"INFO"``) or int.

    Returns:
        The corresponding numeric level.

    Raises:
        ValueError: If *level* is a string that does not match any
            standard logging level name.
    """
    if isinstance(level, int):
        return level
    numeric = logging.getLevelName(level.upper())
    if not isinstance(numeric, int):
        msg = f"Unknown logging level: {level!r}"
        raise ValueError(msg)
    return numeric


def _build_formatter() -> logging.Formatter:
    """Create the standard scribpy log formatter.

    Returns:
        A :class:`logging.Formatter` with timestamp, level, logger
        name, and message.
    """
    return logging.Formatter(_DEFAULT_FORMAT, datefmt=_DATE_FORMAT)


def _make_stream_handler(
    level: int,
) -> logging.StreamHandler:  # type: ignore[type-arg]
    """Create a stderr stream handler.

    Args:
        level: Minimum level for emitted records.

    Returns:
        A configured :class:`logging.StreamHandler`.
    """
    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(_build_formatter())
    return handler


def _make_file_handler(
    path: Path,
    level: int,
) -> logging.FileHandler:
    """Create a file handler.

    Args:
        path: Destination log file (created or appended to).
        level: Minimum level for emitted records.

    Returns:
        A configured :class:`logging.FileHandler`.
    """
    handler = logging.FileHandler(str(path), encoding="utf-8")
    handler.setLevel(level)
    handler.setFormatter(_build_formatter())
    return handler


@contextmanager
def logging_context(
    level: str | int = "INFO",
    *,
    file: Path | None = None,
    console: bool = True,
) -> Iterator[logging.Logger]:
    """Configure the ``"scribpy"`` logger for the duration of a block.

    Handlers added by this context manager are removed on exit so the
    caller's logging configuration is left untouched.

    Args:
        level: Minimum logging level (name or numeric constant).
        file: Optional path to a log file.  When provided a
            :class:`~logging.FileHandler` is attached in addition to
            (or instead of) the console handler.
        console: Whether to emit log records to *stderr*.  Defaults
            to ``True``.

    Yields:
        The configured :class:`logging.Logger` instance.

    Raises:
        ValueError: If *level* is an unrecognised level name.
    """
    numeric_level = _parse_level(level)
    logger = logging.getLogger(_LOGGER_NAME)

    previous_level = logger.level
    logger.setLevel(numeric_level)

    handlers: list[logging.Handler] = []

    if console:
        stream_handler = _make_stream_handler(numeric_level)
        logger.addHandler(stream_handler)
        handlers.append(stream_handler)

    if file is not None:
        file_handler = _make_file_handler(file, numeric_level)
        logger.addHandler(file_handler)
        handlers.append(file_handler)

    try:
        yield logger
    finally:
        for handler in handlers:
            logger.removeHandler(handler)
            handler.close()
        logger.setLevel(previous_level)
