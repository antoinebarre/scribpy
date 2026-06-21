"""Scribpy exception hierarchy.

All exceptions raised by scribpy inherit from :class:`ScribpyError`,
giving callers a single base class to catch when they want to handle
any scribpy-specific failure without catching unrelated errors.
"""


class ScribpyError(Exception):
    """Base exception for all scribpy errors."""


class ImageNotFoundError(ScribpyError):
    """An image referenced in the Markdown source does not exist.

    Attributes:
        path: Filesystem path that was looked up.
    """

    def __init__(self, path: str) -> None:
        """Initialise with the missing image path.

        Args:
            path: Filesystem path that could not be found.
        """
        self.path = path
        super().__init__(f"Image not found: {path}")


class DiagramRenderError(ScribpyError):
    """A diagram block could not be rendered.

    Attributes:
        block_name: Identifier of the failing block.
        engine: Diagram engine (e.g. ``"plantuml"``, ``"mermaid"``).
        mode: Render mode active at the time of failure
            (e.g. ``"web"``, ``"offline"``).
        reason: Human-readable description of the failure cause.
    """

    def __init__(
        self,
        block_name: str,
        engine: str,
        mode: str,
        reason: str,
    ) -> None:
        """Initialise with failure context.

        Args:
            block_name: Identifier of the failing block.
            engine: Diagram engine that failed.
            mode: Active render mode.
            reason: Human-readable failure cause.
        """
        self.block_name = block_name
        self.engine = engine
        self.mode = mode
        self.reason = reason
        super().__init__(block_name, engine, mode, reason)


class InvalidMarkdownError(ScribpyError):
    """The Markdown source is structurally invalid.

    Attributes:
        detail: Description of the structural problem.
    """

    def __init__(self, detail: str) -> None:
        """Initialise with a description of the problem.

        Args:
            detail: What makes the Markdown invalid.
        """
        self.detail = detail
        super().__init__(f"Invalid Markdown: {detail}")
