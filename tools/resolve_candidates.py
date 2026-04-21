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
