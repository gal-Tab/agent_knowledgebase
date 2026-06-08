"""CLI to validate-and-write a single compound learning, then index it.

Reads a learning markdown file (typically an approved draft), validates it via
lib/learning_format, writes it to `<root>/<type-dir>/<id>.md` through the
pre-write gate (invalid content never reaches disk), and updates `<root>/index.md`.

Usage:
    python tools/learning_write.py <learning-file.md> [--root .compound]

Exit code 0 on success (prints the destination path), 1 on validation failure
(prints the errors, writes nothing).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.learning_index import append_entry, entry_from_content
from lib.learning_store import dest_path, write_learning


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate, write, and index a compound learning.")
    parser.add_argument("path", help="Path to the learning .md file (e.g. an approved draft).")
    parser.add_argument("--root", default=".compound", help="Store root (default: ./.compound).")
    args = parser.parse_args(argv)

    src = Path(args.path)
    if not src.exists():
        print(f"error: file not found: {src}", file=sys.stderr)
        return 1

    content = src.read_text()
    root = Path(args.root)

    result = write_learning(root, content)
    if not result.ok:
        print("INVALID — not written:", file=sys.stderr)
        for err in result.errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    dest = dest_path(root, content)
    append_entry(root / "index.md", entry_from_content(content))

    for warn in result.warnings:
        print(f"warning: {warn}", file=sys.stderr)
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
