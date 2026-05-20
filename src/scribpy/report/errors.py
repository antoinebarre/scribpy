"""Custom exceptions for the report generator."""


class ReportDepthError(Exception):
    """Raised when section nesting exceeds H6.

    Attributes:
        current_depth: The heading level that exceeded the maximum.
    """

    def __init__(self, current_depth: int) -> None:
        """Initialize with the offending depth level.

        Args:
            current_depth: The heading level that exceeded H6.
        """
        super().__init__(
            f"Cannot nest further: heading level {current_depth} already at H6 maximum."
        )


class InvalidChildError(TypeError):
    """Raised when an unsupported child type is added to a container.

    Attributes:
        parent_type: Name of the container class.
        child_type: Name of the rejected child class.
    """

    def __init__(self, parent_type: str, child_type: str) -> None:
        """Initialize with parent and child type names.

        Args:
            parent_type: Name of the container class.
            child_type: Name of the rejected child class.
        """
        super().__init__(f"'{child_type}' is not a valid child of '{parent_type}'.")


class InvalidTableError(ValueError):
    """Raised when a Table is constructed with invalid structure.

    Attributes:
        reason: Human-readable explanation of the violation.
    """

    def __init__(self, reason: str) -> None:
        """Initialize with the violation reason.

        Args:
            reason: Human-readable explanation of the structural problem.
        """
        super().__init__(f"Invalid table: {reason}")
