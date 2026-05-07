"""Standalone wiki validator.

Two roles:
  1. Backfill audit: `python tools/validate_wiki.py --all` — validate every
     page in wiki/ and exit non-zero if any errors are found. Used to catch
     pages produced before the pre-write gate landed.
  2. Pre-commit gate (Step 9): pass specific paths
     `python tools/validate_wiki.py path/a.md path/b.md` to validate only the
     files about to be committed.

Skips:
  - wiki/.quarantine/  (known-bad pages awaiting manual review)
  - wiki/index.md, wiki/<category>/_index.md  (generated, no frontmatter)
  - non-.md files
  - paths whose parent directory isn't a known wiki category
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.page_format import ValidationResult, validate_page
from lib.page_writer import infer_page_type
from lib.quarantine import QUARANTINE_DIRNAME

KNOWN_CATEGORIES = {"sources", "entities", "concepts", "comparisons"}
SKIP_FILENAMES = {"index.md", "_index.md"}


def discover_wiki_paths(wiki_root: Path) -> list[Path]:
    """Return all validatable wiki page paths under wiki_root.

    Excludes the quarantine directory and generated index files.
    """
    paths: list[Path] = []
    for category in sorted(KNOWN_CATEGORIES):
        cdir = wiki_root / category
        if not cdir.exists():
            continue
        for md in sorted(cdir.rglob("*.md")):
            if md.name in SKIP_FILENAMES:
                continue
            if QUARANTINE_DIRNAME in md.parts:
                continue
            paths.append(md)
    return paths


def validate_paths(paths: list[Path]) -> dict[Path, ValidationResult]:
    """Validate each path; skip non-md files and paths with unknown categories."""
    results: dict[Path, ValidationResult] = {}
    for path in paths:
        if path.suffix != ".md":
            continue
        if path.name in SKIP_FILENAMES:
            continue
        if QUARANTINE_DIRNAME in path.parts:
            continue
        try:
            page_type = infer_page_type(path)
        except ValueError:
            continue
        try:
            content = path.read_text()
        except FileNotFoundError:
            results[path] = ValidationResult(
                ok=False, errors=[f"file not found: {path}"], warnings=[]
            )
            continue
        results[path] = validate_page(content, page_type)
    return results


def _print_results(results: dict[Path, ValidationResult]) -> int:
    """Print human-readable validation results. Returns count of failed pages."""
    failed = 0
    for path, result in sorted(results.items()):
        if result.ok:
            continue
        failed += 1
        print(f"FAIL {path}")
        for err in result.errors:
            print(f"  - {err}")
    total = len(results)
    passed = total - failed
    print(f"\n{passed}/{total} pages passed", file=sys.stderr)
    return failed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate wiki pages against schema rules.")
    parser.add_argument("paths", nargs="*", type=Path, help="Specific paths to validate.")
    parser.add_argument("--all", action="store_true", help="Validate all pages under --root.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("wiki"),
        help="Wiki root (default: ./wiki).",
    )
    args = parser.parse_args(argv)

    if args.all:
        paths = discover_wiki_paths(args.root)
    else:
        paths = list(args.paths)

    results = validate_paths(paths)
    failed = _print_results(results)
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
