"""Print configured pip-audit vulnerability exceptions."""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from quality_config import load_quality_config


def main() -> None:
    """Print one configured vulnerability ID per line."""
    pyproject_path = Path("pyproject.toml")
    pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    namespace = load_quality_config(pyproject_path).config_namespace

    # Keep the shell runner generic: this script is the small adapter between
    # pyproject configuration and pip-audit's repeated --ignore-vuln flags.
    audit_config = (
        pyproject.get("tool", {}).get(namespace, {}).get("security_audit", {})
    )
    for vuln_id in audit_config.get("ignore_vulns", ()):
        print(vuln_id)


if __name__ == "__main__":
    main()
