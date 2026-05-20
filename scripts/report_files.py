"""Generate the package file listing report with full SHA-256 checksums."""

from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from report_common import base_metadata

from scribpy.report import (
    Chapter,
    Paragraph,
    Report,
    Section,
    Table,
    Text,
    file_checksum,
)

SRC_DIR = Path("src/scribpy")
OUT_PATH = Path("work/reports/report_files.md")
PYPROJECT = Path("pyproject.toml")


def main() -> None:
    """Build the file listing report and write it to work/reports/."""
    src_files = sorted(SRC_DIR.rglob("*.py"))
    test_files = sorted(Path("tests").rglob("*.py"))
    config = _load_pyproject()

    report = (
        Report(
            title="Package File Listing",
            metadata=base_metadata("Package File Listing", "files"),
        )
        .add(_dependencies_chapter(config))
        .add(
            Chapter(title="Source Files")
            .add(
                Paragraph(
                    [
                        Text(f"{len(src_files)} Python files", style="bold"),
                        Text(" found under "),
                        Text("src/scribpy/", style="code"),
                        Text("."),
                    ]
                )
            )
            .add(_file_table(src_files, root=Path("src")))
        )
        .add(
            Chapter(title="Test Files")
            .add(
                Paragraph(
                    [
                        Text(f"{len(test_files)} Python files", style="bold"),
                        Text(" found under "),
                        Text("tests/", style="code"),
                        Text("."),
                    ]
                )
            )
            .add(_file_table(test_files, root=Path(".")))
        )
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report.save(str(OUT_PATH))
    print(f"Written: {OUT_PATH}")


def _load_pyproject() -> dict[str, object]:
    if not PYPROJECT.exists():
        return {}
    with PYPROJECT.open("rb") as f:
        return tomllib.load(f)


def _file_table(files: list[Path], root: Path) -> Section:
    rows = []
    for f in files:
        rel = f.relative_to(root)
        try:
            digest = file_checksum(f, algorithm="sha256")
        except OSError:
            digest = "error"
        size = f"{f.stat().st_size:,} B"
        rows.append([str(rel), size, digest])

    return Section(title="File Inventory").add(
        Table(
            headers=["File", "Size", "SHA-256"],
            rows=rows,
        )
    )


def _installed_packages() -> dict[str, str]:
    """Return {package_name: version} from the active environment."""
    try:
        out = subprocess.check_output(
            [sys.executable, "-m", "pip", "list", "--format=freeze"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        result: dict[str, str] = {}
        for line in out.splitlines():
            if "==" in line:
                name, version = line.split("==", 1)
                result[name.lower()] = version.strip()
        return result
    except Exception:
        return {}


def _dependencies_chapter(config: dict[str, object]) -> Chapter:
    installed = _installed_packages()
    project = config.get("project", {})
    runtime_specs = list(project.get("dependencies", []))  # type: ignore[union-attr]
    dev_specs = list(
        config.get("dependency-groups", {}).get("dev", [])  # type: ignore[union-attr]
    )

    def _resolve(specs: list[str]) -> list[list[str]]:
        rows = []
        for spec in specs:
            # Extract bare name (before any >= <= == ~= etc.)
            bare = (
                spec.split(">=")[0]
                .split("<=")[0]
                .split("==")[0]
                .split("~=")[0]
            )
            bare = bare.strip()
            actual = installed.get(bare.lower(), "not installed")
            rows.append(
                [bare, spec.replace(bare, "").strip() or "any", actual]
            )
        return rows

    runtime_rows = _resolve(runtime_specs)
    dev_rows = _resolve(dev_specs)

    return (
        Chapter(title="Dependencies")
        .add(
            Section(title="Runtime Dependencies").add(
                Table(
                    headers=["Package", "Constraint", "Installed"],
                    rows=runtime_rows,
                )
            )
        )
        .add(
            Section(title="Development Dependencies").add(
                Table(
                    headers=["Package", "Constraint", "Installed"],
                    rows=dev_rows,
                )
            )
        )
    )


if __name__ == "__main__":
    main()
