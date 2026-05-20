"""Shared project-level configuration for quality-gate scripts."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class QualityConfig:
    """Project identity used by all quality-gate scripts.

    Attributes:
        project_name: Human-readable project name used in report titles.
        source_root: Path to the package source directory (e.g. ``src/myapp``).
        source_base: Parent of ``source_root`` used by init-module checks.
        config_namespace: Key under ``[tool]`` where project-specific config
            lives (e.g. ``"myapp"`` reads ``[tool.myapp.code_metrics]``).
    """

    project_name: str
    source_root: Path
    source_base: Path
    config_namespace: str


def load_quality_config(
    pyproject_path: Path = Path("pyproject.toml"),
) -> QualityConfig:
    """Load quality-gate configuration from ``pyproject.toml``.

    Reads ``[tool.quality-gate]`` when present. Falls back to deriving
    values from ``[project].name`` so projects without the section still work.

    Args:
        pyproject_path: Path to the project's ``pyproject.toml``.

    Returns:
        Populated ``QualityConfig`` instance.
    """
    if not pyproject_path.exists():
        return _default_config("project")

    with pyproject_path.open("rb") as fh:
        data = tomllib.load(fh)

    gate = data.get("tool", {}).get("quality-gate", {})

    # Derive a sensible default project name from [project].name when the
    # quality-gate section is absent or incomplete.
    fallback_name: str = (
        str(data.get("project", {}).get("name", "project"))
        .lower()
        .replace("-", "_")
    )

    project_name: str = str(gate.get("project_name", fallback_name))
    config_namespace: str = str(gate.get("config_namespace", fallback_name))
    source_root = Path(str(gate.get("source_root", f"src/{fallback_name}")))
    source_base = Path(str(gate.get("source_base", source_root.parent)))

    return QualityConfig(
        project_name=project_name,
        source_root=source_root,
        source_base=source_base,
        config_namespace=config_namespace,
    )


def _default_config(name: str) -> QualityConfig:
    return QualityConfig(
        project_name=name,
        source_root=Path(f"src/{name}"),
        source_base=Path("src"),
        config_namespace=name,
    )
