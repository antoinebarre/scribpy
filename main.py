"""Interactive demo of scribpy.utils file and generator utilities."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from scribpy.utils import (
    MarkdownConfig,
    generate_markdown,
    is_md_file,
    list_md_files,
    read_md_file,
    write_md_file,
)


def _section(title: str) -> None:
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")


def demo_is_md_file(tmp: Path) -> None:
    _section("is_md_file")

    md_file = tmp / "note.md"
    md_file.write_text("# Note")
    txt_file = tmp / "note.txt"
    txt_file.write_text("plain text")

    print(f"  is_md_file({md_file.name!r})  → {is_md_file(md_file)}")
    print(f"  is_md_file({txt_file.name!r}) → {is_md_file(txt_file)}")
    print(f"  is_md_file('ghost.md')        → {is_md_file(tmp / 'ghost.md')}")


def demo_list_md_files(tmp: Path) -> None:
    _section("list_md_files")

    (tmp / "a.md").write_text("# A")
    (tmp / "b.md").write_text("# B")
    (tmp / "ignore.txt").write_text("not md")
    sub = tmp / "sub"
    sub.mkdir()
    (sub / "c.md").write_text("# C")

    recursive = list_md_files(tmp, recursive=True)
    flat = list_md_files(tmp, recursive=False)

    print(f"  recursive=True  → {[p.name for p in recursive]}")
    print(f"  recursive=False → {[p.name for p in flat]}")


def demo_read_md_file(tmp: Path) -> None:
    _section("read_md_file")

    content = "# Hello\n\nThis is a **Markdown** document."
    f = tmp / "hello.md"
    f.write_text(content, encoding="utf-8")

    result = read_md_file(f)
    print(f"  read {f.name!r} ({f.stat().st_size} bytes):")
    for line in result.splitlines():
        print(f"    {line}")

    try:
        read_md_file(tmp / "missing.md")
    except FileNotFoundError as e:
        print(f"  FileNotFoundError → {e}")

    try:
        read_md_file(tmp / "ignore.txt")
    except ValueError as e:
        print(f"  ValueError        → {e}")


def demo_write_md_file(tmp: Path) -> None:
    _section("write_md_file")

    out = tmp / "output.md"
    write_md_file(out, "# Generated\n\nCreated by scribpy.")
    print(f"  wrote {out.name!r} → {out.read_text()!r}")

    nested = tmp / "deep" / "nested" / "doc.md"
    write_md_file(nested, "# Nested", create_parents=True)
    print(f"  wrote nested path → {nested.relative_to(tmp)}")

    try:
        write_md_file(tmp / "no_dir" / "doc.md", "# X")
    except FileNotFoundError as e:
        print(f"  FileNotFoundError → {e}")

    try:
        write_md_file(tmp / "doc.txt", "# X")
    except ValueError as e:
        print(f"  ValueError        → {e}")


_WORK_DIR = Path(__file__).parent / "work"


def demo_generator() -> None:
    _section("generate_markdown")

    # --- default config (all sections) ---
    doc = generate_markdown(seed=42)
    size_kb = len(doc.encode()) / 1024
    out = _WORK_DIR / "lorem.md"
    write_md_file(out, doc)
    print(f"  seed=42  → {len(doc.splitlines())} lines, {size_kb:.1f} KB → {out}")
    print("  First 3 lines:")
    for line in doc.splitlines()[:3]:
        print(f"    {line}")

    # --- minimal config (no optional sections) ---
    cfg_minimal = MarkdownConfig(
        include_math=False,
        include_mermaid=False,
        include_alerts=False,
        include_footnotes=False,
        include_details=False,
    )
    doc_minimal = generate_markdown(seed=42, config=cfg_minimal)
    out_minimal = _WORK_DIR / "lorem_minimal.md"
    write_md_file(out_minimal, doc_minimal)
    size_min = len(doc_minimal.encode()) / 1024
    print(
        f"  minimal  → {len(doc_minimal.splitlines())} lines, "
        f"{size_min:.1f} KB → {out_minimal}"
    )

    # --- custom separator ---
    cfg_sep = MarkdownConfig(section_separator="\n\n* * *\n\n")
    doc_sep = generate_markdown(seed=0, config=cfg_sep)
    sep_count = doc_sep.count("* * *")
    print(f"  custom separator '* * *' appears {sep_count} time(s)")


def main() -> None:
    print("scribpy — utils demo")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        demo_is_md_file(tmp)
        demo_list_md_files(tmp)
        demo_read_md_file(tmp)
        demo_write_md_file(tmp)
        demo_generator()

    print("\nDone.")


if __name__ == "__main__":
    main()
