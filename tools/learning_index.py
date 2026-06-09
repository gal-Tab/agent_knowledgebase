"""CLI for the compound-learnings index — the single owner of index.md.

Only this tool edits a store's index.md. The /learn-capture command and any
approval path call `append` after writing a learning; nothing else hand-edits
the index (mirrors the manifest-owner discipline in wiki-compile).

Usage:
    python tools/learning_index.py append <learning-file.md>
    python tools/learning_index.py rebuild [--root <store-root>]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.learning_index import append_entry, entry_from_content, rebuild
from lib.learning_store import project_root


def _cmd_append(args: argparse.Namespace) -> int:
    learning_path = Path(args.path).resolve()
    if not learning_path.exists():
        print(f"error: learning file not found: {learning_path}", file=sys.stderr)
        return 1
    # A learning lives at <root>/<type-dir>/<id>.md → root is two parents up.
    store_root = learning_path.parent.parent
    entry = entry_from_content(learning_path.read_text())
    if not entry.get("id") or not entry.get("type"):
        print(f"error: {learning_path} is missing id/type frontmatter", file=sys.stderr)
        return 1
    append_entry(store_root / "index.md", entry)
    print(f"indexed {entry['id']} -> {store_root / 'index.md'}")
    return 0


def _cmd_rebuild(args: argparse.Namespace) -> int:
    root = Path(args.root) if args.root else project_root(Path.cwd())
    if not root.exists():
        print(f"error: store root does not exist: {root}", file=sys.stderr)
        return 1
    text = rebuild(root)
    learning_lines = sum(1 for line in text.splitlines() if line.startswith("- ["))
    print(f"rebuilt {root / 'index.md'} ({learning_lines} learnings)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage the compound-learnings index.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_append = sub.add_parser("append", help="Add/update one learning's index line.")
    p_append.add_argument("path", help="Path to the learning .md file.")
    p_append.set_defaults(func=_cmd_append)

    p_rebuild = sub.add_parser("rebuild", help="Full rebuild of a store's index.md.")
    p_rebuild.add_argument("--root", help="Store root (default: ./.compound).")
    p_rebuild.set_defaults(func=_cmd_rebuild)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
