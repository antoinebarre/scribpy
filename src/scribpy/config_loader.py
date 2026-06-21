"""Configuration loading with three-level cascade.

Priority (highest wins):

1. **API overrides** — explicit :class:`ScribpyConfig` passed by the
   caller.
2. **Local file** — ``scribpy.toml`` in the project directory.
3. **pyproject.toml** — ``[tool.scribpy]`` section.

Each layer provides a partial dictionary.  Layers are merged bottom-up:
pyproject defaults are overridden by the local file, which is overridden
by API parameters.  Fields absent from every layer fall back to the
:class:`ScribpyConfig` dataclass defaults.
"""

from __future__ import annotations

import logging
import tomllib
from pathlib import Path
from typing import Any

from scribpy.config import (
    DEFAULT_CSS_PATH,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_OUTPUT_FORMAT,
    DEFAULT_PLANTUML_JAR,
    DEFAULT_RENDER_MODE,
    DEFAULT_SOURCE,
    DEFAULT_TOC_ENABLED,
    CssConfig,
    DiagramConfig,
    OutputFormat,
    RenderMode,
    ScribpyConfig,
    TocConfig,
)

_log = logging.getLogger(__name__)

_SCRIBPY_TOML = "scribpy.toml"
_PYPROJECT_TOML = "pyproject.toml"


def _read_toml(path: Path) -> dict[str, Any]:
    """Read a TOML file and return its contents as a dictionary.

    Args:
        path: Filesystem path to the TOML file.

    Returns:
        Parsed TOML content.  An empty dict if the file does not exist.
    """
    if not path.is_file():
        return {}
    _log.debug("Reading config from %s", path)
    with path.open("rb") as fh:
        return tomllib.load(fh)


def _read_pyproject_section(root: Path) -> dict[str, Any]:
    """Extract the ``[tool.scribpy]`` section from pyproject.toml.

    Args:
        root: Project root directory containing ``pyproject.toml``.

    Returns:
        The ``tool.scribpy`` mapping, or an empty dict if absent.
    """
    data = _read_toml(root / _PYPROJECT_TOML)
    section: dict[str, Any] = data.get("tool", {}).get("scribpy", {})
    return section


def _read_local_config(root: Path) -> dict[str, Any]:
    """Read the project-local ``scribpy.toml`` file.

    Args:
        root: Project root directory.

    Returns:
        Parsed content, or an empty dict if the file is absent.
    """
    return _read_toml(root / _SCRIBPY_TOML)


def _merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge *overlay* into *base*.

    Nested dicts are merged; all other values are replaced.

    Args:
        base: Lower-priority mapping (mutated in place).
        overlay: Higher-priority mapping.

    Returns:
        The merged mapping (same object as *base*).
    """
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge(base[key], value)
        else:
            base[key] = value
    return base


def _parse_css(raw: dict[str, Any]) -> CssConfig:
    """Build a :class:`CssConfig` from a raw TOML mapping.

    Args:
        raw: The ``css`` sub-table from the config file.

    Returns:
        A frozen :class:`CssConfig`.
    """
    path = raw.get("path")
    return CssConfig(path=Path(path) if path is not None else DEFAULT_CSS_PATH)


def _parse_toc(raw: dict[str, Any]) -> TocConfig:
    """Build a :class:`TocConfig` from a raw TOML mapping.

    Args:
        raw: The ``toc`` sub-table from the config file.

    Returns:
        A frozen :class:`TocConfig`.
    """
    return TocConfig(
        enabled=bool(raw.get("enabled", DEFAULT_TOC_ENABLED)),
    )


def _parse_diagrams(raw: dict[str, Any]) -> DiagramConfig:
    """Build a :class:`DiagramConfig` from a raw TOML mapping.

    Args:
        raw: The ``diagrams`` sub-table from the config file.

    Returns:
        A frozen :class:`DiagramConfig`.
    """
    mode_str = raw.get("render_mode")
    mode = (
        RenderMode(mode_str)
        if mode_str is not None
        else RenderMode(DEFAULT_RENDER_MODE)
    )
    jar = raw.get("plantuml_jar")
    return DiagramConfig(
        render_mode=mode,
        plantuml_jar=Path(jar) if jar is not None else DEFAULT_PLANTUML_JAR,
    )


def _build_config(raw: dict[str, Any]) -> ScribpyConfig:
    """Convert a merged raw mapping into a :class:`ScribpyConfig`.

    Args:
        raw: Flat or nested mapping produced by merging all layers.

    Returns:
        A frozen :class:`ScribpyConfig`.
    """
    source = raw.get("source")
    output_dir = raw.get("output_dir")
    fmt = raw.get("output_format")

    return ScribpyConfig(
        source=Path(source) if source is not None else DEFAULT_SOURCE,
        output_dir=(
            Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT_DIR
        ),
        output_format=(
            OutputFormat(fmt)
            if fmt is not None
            else OutputFormat(DEFAULT_OUTPUT_FORMAT)
        ),
        css=_parse_css(raw.get("css", {})),
        toc=_parse_toc(raw.get("toc", {})),
        diagrams=_parse_diagrams(raw.get("diagrams", {})),
    )


def _config_to_dict(cfg: ScribpyConfig) -> dict[str, Any]:
    """Serialize a :class:`ScribpyConfig` to a plain dict for merging.

    Args:
        cfg: The configuration to serialize.

    Returns:
        A nested dict matching the TOML structure.
    """
    return {
        "source": str(cfg.source),
        "output_dir": str(cfg.output_dir),
        "output_format": cfg.output_format.value,
        "css": {
            "path": str(cfg.css.path) if cfg.css.path is not None else None,
        },
        "toc": {"enabled": cfg.toc.enabled},
        "diagrams": {
            "render_mode": cfg.diagrams.render_mode.value,
            "plantuml_jar": (
                str(cfg.diagrams.plantuml_jar)
                if cfg.diagrams.plantuml_jar is not None
                else None
            ),
        },
    }


def load_config(
    root: Path | None = None,
    *,
    overrides: ScribpyConfig | None = None,
) -> ScribpyConfig:
    """Load configuration with three-level cascade.

    Priority (highest first): *overrides* > ``scribpy.toml`` >
    ``pyproject.toml [tool.scribpy]``.

    Args:
        root: Project root directory.  Defaults to the current working
            directory.
        overrides: Explicit API-level configuration.  Fields set here
            take precedence over file-based configuration.

    Returns:
        A fully resolved :class:`ScribpyConfig`.
    """
    root = root or Path.cwd()

    layer_pyproject = _read_pyproject_section(root)
    layer_local = _read_local_config(root)

    merged: dict[str, Any] = {}
    _merge(merged, layer_pyproject)
    _log.debug("After pyproject.toml: %s", merged)

    _merge(merged, layer_local)
    _log.debug("After scribpy.toml: %s", merged)

    if overrides is not None:
        _merge(merged, _config_to_dict(overrides))
        _log.debug("After API overrides: %s", merged)

    return _build_config(merged)
