"""Tests for scribpy.log — logging context manager."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from scribpy.log import (
    _LOGGER_NAME,
    _parse_level,
    logging_context,
)


class TestParseLevel:
    """Tests for the _parse_level helper."""

    def test_string_info(self) -> None:
        """Requirement: 'INFO' maps to logging.INFO."""
        assert _parse_level("INFO") == logging.INFO

    def test_string_case_insensitive(self) -> None:
        """Requirement: level names are case-insensitive."""
        assert _parse_level("debug") == logging.DEBUG

    def test_integer_passthrough(self) -> None:
        """Requirement: numeric levels pass through unchanged."""
        assert _parse_level(logging.WARNING) == logging.WARNING

    def test_unknown_string_raises(self) -> None:
        """Requirement: unknown level name raises ValueError."""
        with pytest.raises(ValueError, match="Unknown logging level"):
            _parse_level("BOGUS")


class TestLoggingContext:
    """Tests for the logging_context context manager."""

    def test_yields_logger(self) -> None:
        """Requirement: context yields the 'scribpy' logger."""
        with logging_context() as logger:
            assert logger.name == _LOGGER_NAME

    def test_handlers_added_inside_block(self) -> None:
        """Requirement: handlers are present during the block."""
        logger = logging.getLogger(_LOGGER_NAME)
        before = len(logger.handlers)
        with logging_context():
            assert len(logger.handlers) == before + 1
        assert len(logger.handlers) == before

    def test_handlers_removed_after_block(self) -> None:
        """Requirement: no handler leaks after the block."""
        logger = logging.getLogger(_LOGGER_NAME)
        handlers_before = list(logger.handlers)
        with logging_context():
            pass
        assert logger.handlers == handlers_before

    def test_level_restored_after_block(self) -> None:
        """Requirement: logger level is restored on exit."""
        logger = logging.getLogger(_LOGGER_NAME)
        original_level = logger.level
        with logging_context(level="DEBUG"):
            assert logger.level == logging.DEBUG
        assert logger.level == original_level

    def test_console_output(self, capfd: pytest.CaptureFixture[str]) -> None:
        """Requirement: console handler writes to stderr."""
        with logging_context(level="INFO") as logger:
            logger.info("hello from scribpy")
        captured = capfd.readouterr()
        assert "hello from scribpy" in captured.err

    def test_console_disabled(
        self,
        capfd: pytest.CaptureFixture[str],
    ) -> None:
        """Requirement: console=False suppresses stderr output."""
        with logging_context(level="INFO", console=False) as logger:
            logger.info("should not appear")
        captured = capfd.readouterr()
        assert "should not appear" not in captured.err

    def test_file_handler(self, tmp_path: Path) -> None:
        """Requirement: file parameter writes log records to a file."""
        log_file = tmp_path / "test.log"
        with logging_context(
            level="INFO",
            file=log_file,
            console=False,
        ) as logger:
            logger.info("file entry")
        content = log_file.read_text(encoding="utf-8")
        assert "file entry" in content

    def test_file_handler_closed_after_block(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: file handler is closed on exit."""
        log_file = tmp_path / "closed.log"
        logger = logging.getLogger(_LOGGER_NAME)
        with logging_context(file=log_file, console=False):
            pass
        for handler in logger.handlers:
            assert not isinstance(handler, logging.FileHandler)

    def test_handlers_removed_on_exception(self) -> None:
        """Requirement: handlers are cleaned up even on exception."""
        logger = logging.getLogger(_LOGGER_NAME)
        handlers_before = list(logger.handlers)
        with pytest.raises(RuntimeError, match="boom"), logging_context():
            raise RuntimeError("boom")
        assert logger.handlers == handlers_before

    def test_child_logger_inherits_config(
        self,
        capfd: pytest.CaptureFixture[str],
    ) -> None:
        """Requirement: child loggers benefit from the context."""
        child = logging.getLogger(f"{_LOGGER_NAME}.core.parser")
        with logging_context(level="INFO"):
            child.info("parsed 3 documents")
        captured = capfd.readouterr()
        assert "parsed 3 documents" in captured.err

    def test_below_level_not_emitted(
        self,
        capfd: pytest.CaptureFixture[str],
    ) -> None:
        """Requirement: records below the level are suppressed."""
        with logging_context(level="WARNING") as logger:
            logger.info("should be suppressed")
        captured = capfd.readouterr()
        assert "should be suppressed" not in captured.err

    def test_format_contains_timestamp_and_level(
        self,
        capfd: pytest.CaptureFixture[str],
    ) -> None:
        """Requirement: log format includes timestamp and level."""
        with logging_context(level="INFO") as logger:
            logger.info("check format")
        line = capfd.readouterr().err.strip()
        assert "INFO" in line
        assert "|" in line
