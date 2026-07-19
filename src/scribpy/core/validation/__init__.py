"""Project validation public interface."""

from scribpy.core.validation.engine import validate_project
from scribpy.core.validation.model import (
    ProjectDiagnostic,
    ProjectValidationReport,
)

__all__ = [
    "ProjectDiagnostic",
    "ProjectValidationReport",
    "validate_project",
]
