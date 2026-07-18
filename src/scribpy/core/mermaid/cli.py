"""Mermaid renderer backed by the official Mermaid CLI."""

from __future__ import annotations

import asyncio
import shutil
import tempfile
from pathlib import Path
from typing import cast

from scribpy.errors import MermaidRenderError

_DEFAULT_COMMAND = "mmdc"
_RENDER_TIMEOUT_SECONDS = 60


class MermaidCliRenderer:
    """Render Mermaid diagrams with the official ``mmdc`` executable.

    Attributes:
        command: Executable name or path used to invoke Mermaid CLI.
    """

    def __init__(self, command: str = _DEFAULT_COMMAND) -> None:
        """Initialize a Mermaid CLI renderer.

        Args:
            command: Mermaid CLI executable name or path.
        """
        self.command = command

    def render(self, diagram: str) -> bytes:
        """Render one Mermaid diagram to PNG.

        Args:
            diagram: Mermaid source without fenced code delimiters.

        Returns:
            Rendered PNG bytes.

        Raises:
            MermaidRenderError: If the executable is missing, fails, times
                out, or does not produce a PNG file.
        """
        executable = shutil.which(self.command)
        if executable is None:
            detail = f"Mermaid CLI executable not found: {self.command}"
            raise MermaidRenderError(detail)
        with tempfile.TemporaryDirectory(prefix="scribpy-mermaid-") as temp:
            return self._render_in(Path(temp), executable, diagram)

    def _render_in(
        self,
        temp_dir: Path,
        executable: str,
        diagram: str,
    ) -> bytes:
        """Render one diagram inside an isolated temporary directory.

        Args:
            temp_dir: Temporary directory for source and output files.
            executable: Resolved absolute Mermaid CLI executable path.
            diagram: Mermaid source without fenced code delimiters.

        Returns:
            Rendered PNG bytes.

        Raises:
            MermaidRenderError: If CLI execution or PNG production fails.
        """
        source = temp_dir / "diagram.mmd"
        output = temp_dir / "diagram.png"
        source.write_text(diagram, encoding="utf-8")
        command = [
            executable,
            "--input",
            str(source),
            "--output",
            str(output),
            "--backgroundColor",
            "transparent",
        ]
        try:
            return_code, stderr = _execute(command)
        except OSError as exc:
            detail = f"Mermaid CLI execution failed: {exc}"
            raise MermaidRenderError(detail) from exc
        if return_code != 0:
            error_detail = stderr.strip() or "no error output"
            detail = f"Mermaid CLI exited with {return_code}: {error_detail}"
            raise MermaidRenderError(detail)
        if not output.is_file():
            detail = "Mermaid CLI completed without producing a PNG"
            raise MermaidRenderError(detail)
        return output.read_bytes()


def _execute(command: list[str]) -> tuple[int, str]:
    """Execute Mermaid CLI without a shell.

    Args:
        command: Resolved executable and Mermaid CLI arguments.

    Returns:
        Process return code and decoded standard error.

    Raises:
        OSError: If the executable cannot be started.
        TimeoutError: If Mermaid CLI exceeds the rendering timeout.
    """
    return asyncio.run(_execute_async(command))


async def _execute_async(command: list[str]) -> tuple[int, str]:
    """Execute Mermaid CLI asynchronously with a timeout.

    Args:
        command: Resolved executable and Mermaid CLI arguments.

    Returns:
        Process return code and decoded standard error.

    Raises:
        OSError: If the executable cannot be started.
        TimeoutError: If Mermaid CLI exceeds the rendering timeout.
    """
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        _, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=_RENDER_TIMEOUT_SECONDS,
        )
    except TimeoutError:
        process.kill()
        await process.wait()
        raise
    return_code = cast("int", process.returncode)
    return return_code, stderr.decode("utf-8", errors="replace")


__all__ = ["MermaidCliRenderer"]
