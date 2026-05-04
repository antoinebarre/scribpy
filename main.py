"""Interactive demo of scribpy.utils file utilities."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from scribpy.utils import is_md_file, list_md_files, read_md_file, write_md_file


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


def main() -> None:
    print("scribpy — utils demo")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        demo_is_md_file(tmp)
        demo_list_md_files(tmp)
        demo_read_md_file(tmp)
        demo_write_md_file(tmp)

    print("\nDone.")


if __name__ == "__main__":
    main()
