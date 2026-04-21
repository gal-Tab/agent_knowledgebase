"""Batch resolution candidate collector for kb-compile.

Parses Extracted References from source pages, deduplicates by slug,
classifies as CREATE/UPDATE/SKIP, and outputs a markdown resolution brief.
"""
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "lib"))

from slug import slug_entity, slug_concept
from page_format import parse_frontmatter

_ENTITY_RE = re.compile(
    r"^- Entity:\s*(.+?)\s*—\s*(.+?)\s*\(type:\s*(\w+)\)\s*$"
)
_CONCEPT_RE = re.compile(
    r"^- Concept:\s*(.+?)\s*—\s*(.+?)\s*$"
)


def parse_extracted_references(content: str, source_slug: str) -> list[dict]:
    """Parse the Extracted References section from a source page.

    Returns list of candidate dicts with keys:
    kind, name, description, source_slug, entity_type (for entities only).
    """
    if not content:
        return []

    marker = "## Extracted References"
    idx = content.find(marker)
    if idx == -1:
        return []

    section = content[idx + len(marker):]
    next_heading = re.search(r"^## ", section, re.MULTILINE)
    if next_heading:
        section = section[:next_heading.start()]

    candidates = []
    for line in section.strip().split("\n"):
        line = line.strip()
        m = _ENTITY_RE.match(line)
        if m:
            candidates.append({
                "kind": "entity",
                "name": m.group(1).strip(),
                "description": m.group(2).strip(),
                "entity_type": m.group(3).strip(),
                "source_slug": source_slug,
            })
            continue
        m = _CONCEPT_RE.match(line)
        if m:
            candidates.append({
                "kind": "concept",
                "name": m.group(1).strip(),
                "description": m.group(2).strip(),
                "entity_type": None,
                "source_slug": source_slug,
            })
    return candidates


def deduplicate_candidates(candidates: list[dict]) -> list[dict]:
    """Merge candidates with the same slug across sources.

    Returns list of deduplicated dicts with keys:
    kind, name, slug, entity_type, sources (list), descriptions (dict of source_slug: desc).
    """
    if not candidates:
        return []

    by_slug = {}
    for c in candidates:
        if c["kind"] == "entity":
            slug = slug_entity(c["name"], c["entity_type"])
        else:
            slug = slug_concept(c["name"])

        if slug not in by_slug:
            by_slug[slug] = {
                "kind": c["kind"],
                "name": c["name"],
                "slug": slug,
                "entity_type": c["entity_type"],
                "sources": [],
                "descriptions": {},
            }

        entry = by_slug[slug]
        if c["source_slug"] not in entry["sources"]:
            entry["sources"].append(c["source_slug"])
        entry["descriptions"][c["source_slug"]] = c["description"]

    return list(by_slug.values())
