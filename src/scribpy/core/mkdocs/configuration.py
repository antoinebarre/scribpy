"""MkDocs static YAML configuration writing."""

from __future__ import annotations

from pathlib import Path

import yaml

Navigation = list[dict[str, object]]


def write_configuration(
    path: Path,
    site_name: str,
    navigation: Navigation,
) -> None:
    """Write a static MkDocs YAML configuration.

    Args:
        path: Destination ``mkdocs.yml`` path.
        site_name: MkDocs site display name.
        navigation: Ordered hierarchical MkDocs navigation.

    Raises:
        OSError: If the configuration cannot be written.
    """
    configuration: dict[str, object] = {
        "site_name": site_name,
        "docs_dir": "docs",
        "nav": navigation,
    }
    path.write_text(
        yaml.safe_dump(
            configuration,
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
