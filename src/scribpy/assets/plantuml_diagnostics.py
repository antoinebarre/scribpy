"""User-facing PlantUML diagnostics."""

from __future__ import annotations

from scribpy.assets.plantuml_types import PlantUmlRenderError
from scribpy.model import Diagnostic


def java_missing_diagnostic(detail: str) -> Diagnostic:
    """Create the early Java-environment diagnostic.

    Args:
        detail: Reason the local Java renderer is unavailable.

    Returns:
        A diagnostic suitable for preflight validation.
    """
    return Diagnostic(
        severity="error",
        code="UML004",
        message=f"Java PlantUML renderer is unavailable: {detail}",
        hint=(
            "Install a Java runtime and ensure `java` is available on PATH, "
            "or configure builders.html.plantuml.renderer = 'web'."
        ),
    )


def render_failure_diagnostic(error: PlantUmlRenderError) -> Diagnostic:
    """Return a backend-specific PlantUML render diagnostic.

    Args:
        error: Typed renderer error.

    Returns:
        Web or Java render diagnostic.
    """
    if error.backend == "web":
        return Diagnostic(
            severity="error",
            code="UML005",
            message=f"PlantUML web rendering failed: {error}",
            hint=(
                "Check builders.html.plantuml.server_url and server policy, "
                "or use a self-hosted PlantUML server."
            ),
        )
    return java_render_failure_diagnostic(str(error))


def java_render_failure_diagnostic(detail: str) -> Diagnostic:
    """Return a Java-renderer failure diagnostic.

    Args:
        detail: Renderer failure detail.

    Returns:
        Diagnostic for a local PlantUML rendering failure.
    """
    return Diagnostic(
        severity="error",
        code="UML002",
        message=f"Cannot render PlantUML block: {detail}",
        hint=(
            "Ensure the bundled PlantUML runtime can execute through Java and "
            "the diagram syntax is valid."
        ),
    )


__all__ = [
    "java_missing_diagnostic",
    "java_render_failure_diagnostic",
    "render_failure_diagnostic",
]
