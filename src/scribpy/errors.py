"""Scribpy exception hierarchy."""


class ScribpyError(Exception):
    """Base exception for all scribpy domain failures."""


class ScribpyManifestWarning(UserWarning):
    """Warning emitted for ignored scribpy.yml manifest settings."""


class InvalidScribpyManifestError(ScribpyError):
    """The scribpy.yml manifest is invalid.

    Attributes:
        path: Manifest file path.
        detail: Description of the manifest problem.
    """

    def __init__(self, path: str, detail: str) -> None:
        """Initialise with manifest path and problem detail.

        Args:
            path: Manifest file path.
            detail: What makes the manifest invalid.
        """
        self.path = path
        self.detail = detail
        super().__init__(path, detail)


class PlantUmlRenderError(ScribpyError):
    """A PlantUML diagram could not be rendered.

    Attributes:
        detail: Description of the rendering failure.
    """

    def __init__(self, detail: str) -> None:
        """Initialise with a description of the rendering failure.

        Args:
            detail: What caused the rendering to fail.
        """
        self.detail = detail
        super().__init__(f"PlantUML render error: {detail}")


class MermaidRenderError(ScribpyError):
    """A Mermaid diagram could not be rendered.

    Attributes:
        detail: Description of the rendering failure.
    """

    def __init__(self, detail: str) -> None:
        """Initialise with a description of the rendering failure.

        Args:
            detail: What caused the rendering to fail.
        """
        self.detail = detail
        super().__init__(f"Mermaid render error: {detail}")


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
