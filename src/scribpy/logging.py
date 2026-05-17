"""Public logging configuration for Scribpy execution traces."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path

_LOGGER_NAME = "scribpy"
_DEFAULT_LOG_RELATIVE_PATH = Path("build/logs/scribpy.log")
_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


@dataclass(frozen=True)
class LoggingSettings:
    """Active logging settings for the current execution context.

    Attributes:
        level: Logging level accepted by :mod:`logging`.
        console: Whether to emit logs to stderr.
        file: Whether to emit logs to a file.
        file_path: Optional custom file path. Relative paths are resolved from
            the project root once it becomes known.
    """

    level: str | int = "INFO"
    console: bool = False
    file: bool = True
    file_path: Path | None = None


_SETTINGS: ContextVar[LoggingSettings | None] = ContextVar(
    "scribpy_logging_settings", default=None
)
_HANDLERS: ContextVar[tuple[logging.Handler, ...]] = ContextVar(
    "scribpy_logging_handlers", default=()
)


def get_logger(name: str) -> logging.Logger:
    """Return one logger under the Scribpy logger hierarchy.

    Args:
        name: Module or component name.

    Returns:
        Standard-library logger.
    """
    return logging.getLogger(name)


@contextmanager
def logging_context(
    *,
    level: str | int = "INFO",
    console: bool = False,
    file: bool = True,
    file_path: str | Path | None = None,
) -> Iterator[None]:
    """Configure Scribpy logging for a bounded execution context.

    File logging defaults to ``build/logs/scribpy.log`` below the active project
    root. The file handler is created lazily once a chain resolves that root.

    Args:
        level: Logging threshold such as ``"INFO"`` or ``"DEBUG"``.
        console: Whether to emit log records to stderr.
        file: Whether to emit log records to a file.
        file_path: Optional custom log path. Relative paths are interpreted
            relative to the resolved project root.

    Yields:
        Nothing while the logging configuration is active.

    Returns:
        Context manager controlling the active logging handlers.
    """
    logger = logging.getLogger(_LOGGER_NAME)
    old_level = logger.level
    logger.setLevel(level)
    logger.propagate = False

    settings = LoggingSettings(
        level=level,
        console=console,
        file=file,
        file_path=None if file_path is None else Path(file_path),
    )
    settings_token = _SETTINGS.set(settings)
    handlers_token = _HANDLERS.set(())

    if console:
        _attach_handler(logging.StreamHandler())

    try:
        yield
    finally:
        for handler in _HANDLERS.get():
            logger.removeHandler(handler)
            handler.close()
        _HANDLERS.reset(handlers_token)
        _SETTINGS.reset(settings_token)
        logger.setLevel(old_level)


def prepare_logging(project_root: Path) -> Path | None:
    """Create the configured file handler once a project root is available.

    Args:
        project_root: Absolute or relative resolved project root.

    Returns:
        Effective log path when file logging is active, otherwise ``None``.
    """
    settings = _SETTINGS.get()
    if settings is None or not settings.file:
        return None

    if any(isinstance(handler, logging.FileHandler) for handler in _HANDLERS.get()):
        return _effective_log_path(project_root, settings)

    log_path = _effective_log_path(project_root, settings)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    _attach_handler(logging.FileHandler(log_path, encoding="utf-8"))
    return log_path


def logging_enabled() -> bool:
    """Return whether a Scribpy logging context is active.

    Returns:
        Whether logging is currently configured.
    """
    return _SETTINGS.get() is not None


def _attach_handler(handler: logging.Handler) -> None:
    logger = logging.getLogger(_LOGGER_NAME)
    settings = _SETTINGS.get()
    assert settings is not None
    handler.setLevel(settings.level)
    handler.setFormatter(logging.Formatter(_FORMAT))
    logger.addHandler(handler)
    _HANDLERS.set((*_HANDLERS.get(), handler))


def _effective_log_path(project_root: Path, settings: LoggingSettings) -> Path:
    configured = settings.file_path or _DEFAULT_LOG_RELATIVE_PATH
    return configured if configured.is_absolute() else project_root / configured


__all__ = [
    "LoggingSettings",
    "get_logger",
    "logging_context",
    "logging_enabled",
    "prepare_logging",
]
