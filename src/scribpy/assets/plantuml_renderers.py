"""PlantUML renderer backends."""

from __future__ import annotations

import shutil
import subprocess  # nosec B404
from importlib import resources
from typing import cast
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from scribpy.assets.plantuml_diagnostics import java_missing_diagnostic
from scribpy.assets.plantuml_encoding import encode_server_payload
from scribpy.assets.plantuml_types import PlantUmlRenderError
from scribpy.logging import get_logger
from scribpy.model import Diagnostic

logger = get_logger(__name__)


class JavaPlantUmlRenderer:
    """Render PlantUML through the JAR shipped inside Scribpy."""

    def render(self, source: str, output_format: str) -> bytes:
        """Render PlantUML source with the bundled JAR through Java.

        Args:
            source: Raw PlantUML source.
            output_format: Requested PlantUML output format.

        Returns:
            Rendered bytes produced by PlantUML.

        Raises:
            RuntimeError: If PlantUML cannot render the source.
            OSError: If Java cannot be executed.
        """
        jar_path = resources.files("scribpy").joinpath(
            "vendor/plantuml-mit.jar"
        )
        command = (
            "java",
            "-jar",
            str(jar_path),
            f"-t{output_format}",
            "-pipe",
        )
        logger.debug(
            "Executing bundled PlantUML renderer: %s", " ".join(command)
        )
        completed = subprocess.run(
            command,
            input=source.encode("utf-8"),
            capture_output=True,
            check=False,
        )  # nosec B603
        if completed.returncode != 0:
            detail = completed.stderr.decode("utf-8", errors="replace").strip()
            logger.error(
                "Bundled PlantUML renderer failed: %s", detail or "<no stderr>"
            )
            raise PlantUmlRenderError(
                "java", detail or "PlantUML rendering failed."
            )
        logger.debug("Bundled PlantUML renderer completed successfully")
        return completed.stdout


class WebPlantUmlRenderer:
    """Render PlantUML by calling a configured PlantUML web server."""

    _USER_AGENT = "python-plantuml"

    def __init__(self, server_url: str) -> None:
        """Create the web renderer.

        Args:
            server_url: Base PlantUML server URL, without the output path.
        """
        self._server_url = server_url.rstrip("/")

    def render(self, source: str, output_format: str) -> bytes:
        """Render PlantUML source through the configured web server.

        Args:
            source: Raw PlantUML source.
            output_format: Requested PlantUML output format.

        Returns:
            Rendered bytes returned by the server.

        Raises:
            RuntimeError: If the server cannot be reached.
        """
        encoded = encode_server_payload(source)
        url = f"{self._server_url}/{output_format}/{encoded}"
        _validate_http_url(url)
        request = Request(url, headers={"User-Agent": self._USER_AGENT})
        logger.info(
            "Rendering PlantUML through web server %s", self._server_url
        )
        try:
            with urlopen(request, timeout=30) as response:  # nosec B310
                return cast("bytes", response.read())
        except (OSError, URLError) as exc:
            raise PlantUmlRenderError("web", str(exc)) from exc


def validate_java_plantuml_environment() -> tuple[Diagnostic, ...]:
    """Check that Java PlantUML execution can start before the build begins.

    Returns:
        Diagnostics describing an unavailable Java runtime.
    """
    java = shutil.which("java")
    if java is None:
        return (
            java_missing_diagnostic("Could not find the `java` executable."),
        )
    try:
        completed = subprocess.run(
            (java, "-version"),
            capture_output=True,
            check=False,
        )  # nosec B603
    except OSError as exc:
        return (java_missing_diagnostic(f"Could not execute Java: {exc}"),)
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        return (
            java_missing_diagnostic(
                detail
                or f"`java -version` exited with code {completed.returncode}."
            ),
        )
    return ()


def _validate_http_url(url: str) -> None:
    """Validate that a renderer URL targets an HTTP(S) endpoint."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise PlantUmlRenderError(
            "web", "PlantUML renderer URL must use http or https."
        )


__all__ = [
    "JavaPlantUmlRenderer",
    "WebPlantUmlRenderer",
    "validate_java_plantuml_environment",
]
