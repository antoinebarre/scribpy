"""Print configured pip-audit vulnerability exceptions."""

from __future__ import annotations

import tomllib
from pathlib import Path


def main() -> None:
    """Print one configured vulnerability ID per line."""
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    # Keep the shell runner generic: this script is the small adapter between
    # pyproject configuration and pip-audit's repeated --ignore-vuln flags.
    audit_config = (
        pyproject.get("tool", {}).get("scribpy", {}).get("security_audit", {})
    )
    for vuln_id in audit_config.get("ignore_vulns", ()):
        print(vuln_id)


if __name__ == "__main__":
    main()
