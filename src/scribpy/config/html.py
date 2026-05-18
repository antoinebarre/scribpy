"""HTML-specific configuration parsing helpers."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from scribpy.config.types import PlantUmlConfig, PlantUmlRendererMode

type RawSection = Mapping[str, object]


def parse_plantuml_config(
    raw: RawSection,
    *,
    parse_optional_str: Callable[[RawSection, str, str], str | None],
    error_type: type[ValueError],
) -> PlantUmlConfig:
    """Parse PlantUML renderer config.

    Args:
        raw: Raw nested TOML section.
        parse_optional_str: Shared optional-string parser from the loader.
        error_type: Configuration parse exception type.

    Returns:
        Typed PlantUML configuration.
    """
    renderer = raw.get("renderer", "web")
    if renderer not in ("java", "web"):
        raise error_type(
            "Configuration value builders.html.plantuml.renderer must be "
            "'java' or 'web'."
        )
    server_url = parse_optional_str(raw, "server_url", "builders.html.plantuml")
    typed_renderer: PlantUmlRendererMode = renderer
    return PlantUmlConfig(
        renderer=typed_renderer,
        server_url=server_url or PlantUmlConfig().server_url,
    )


__all__ = ["parse_plantuml_config"]
