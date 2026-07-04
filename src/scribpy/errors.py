"""Scribpy exception hierarchy."""


class ScribpyError(Exception):
    """Base exception for all scribpy domain failures."""


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
