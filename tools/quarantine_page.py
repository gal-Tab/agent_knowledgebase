"""CLI wrapper for quarantine operations.

Usage:
  python3 tools/quarantine_page.py move <target_path> <content_file> <errors_file> [--wiki-root WIKI]
      Move <content_file>'s contents to wiki/.quarantine/{category}/{slug}.md with errors sidecar.
      The original <target_path> is left untouched.

  python3 tools/quarantine_page.py recover <quarantined_path> [--wiki-root WIKI]
      Re-validate a quarantined file; on success move it back to its target.

  python3 tools/quarantine_page.py count [--wiki-root WIKI]
      Print the count of quarantined pages.

  python3 tools/quarantine_page.py list [--wiki-root WIKI]
      Print one quarantined page path per line.

Exit codes:
  0 = success (or recovery succeeded)
  1 = failure (validation error on recovery, or other error)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.quarantine import (
    count_quarantined,
    list_quarantined,
    move_to_quarantine,
    recover_from_quarantine,
)


def _cmd_move(args) -> int:
    content = Path(args.content_file).read_text()
    errors_payload = Path(args.errors_file).read_text().strip()
    if errors_payload.startswith("["):
        errors = json.loads(errors_payload)
    else:
        errors = [ln for ln in errors_payload.splitlines() if ln.strip()]
    q_path = move_to_quarantine(
        Path(args.target_path), content, errors, Path(args.wiki_root)
    )
    print(str(q_path))
    return 0


def _cmd_recover(args) -> int:
    result = recover_from_quarantine(Path(args.quarantined_path), Path(args.wiki_root))
    if result.ok:
        print(f"recovered {args.quarantined_path}")
        return 0
    print(f"recovery failed for {args.quarantined_path}", file=sys.stderr)
    for err in result.errors:
        print(f"  - {err}", file=sys.stderr)
    return 1


def _cmd_count(args) -> int:
    print(count_quarantined(Path(args.wiki_root)))
    return 0


def _cmd_list(args) -> int:
    for p in list_quarantined(Path(args.wiki_root)):
        print(str(p))
    return 0


def _add_wiki_root(p: argparse.ArgumentParser) -> None:
    p.add_argument("--wiki-root", default="wiki", help="Wiki root (default: ./wiki).")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Quarantine operations for the wiki-compile pipeline.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_move = sub.add_parser("move")
    p_move.add_argument("target_path")
    p_move.add_argument("content_file")
    p_move.add_argument("errors_file")
    _add_wiki_root(p_move)
    p_move.set_defaults(func=_cmd_move)

    p_rec = sub.add_parser("recover")
    p_rec.add_argument("quarantined_path")
    _add_wiki_root(p_rec)
    p_rec.set_defaults(func=_cmd_recover)

    p_count = sub.add_parser("count")
    _add_wiki_root(p_count)
    p_count.set_defaults(func=_cmd_count)

    p_list = sub.add_parser("list")
    _add_wiki_root(p_list)
    p_list.set_defaults(func=_cmd_list)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
