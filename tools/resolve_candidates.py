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


def _parse_index_slugs(index_content: str) -> dict[str, str]:
    """Extract slug → category mapping from wiki/index.md.

    Parses lines like: - [Title](entities/slug.md) — description
    Returns: {"slug": "entities", ...}
    """
    pattern = re.compile(r"\[.+?\]\((\w+)/([^)]+)\.md\)")
    slugs = {}
    for m in pattern.finditer(index_content):
        category, slug = m.group(1), m.group(2)
        slugs[slug] = category
    return slugs


def _build_alias_map(wiki_path: Path) -> dict[str, str]:
    """Build a mapping of normalized alias → existing slug.

    Scans entity and concept pages for aliases in frontmatter.
    """
    alias_map = {}
    for category in ("entities", "concepts"):
        cat_dir = wiki_path / category
        if not cat_dir.exists():
            continue
        for page in cat_dir.glob("*.md"):
            if page.name.startswith("_"):
                continue
            content = page.read_text()
            fm = parse_frontmatter(content)
            slug = page.stem
            aliases = fm.get("aliases", [])
            if isinstance(aliases, list):
                for alias in aliases:
                    normalized = alias.strip().lower()
                    alias_map[normalized] = slug
    return alias_map


def _get_existing_source_refs(page_path: Path) -> list[str]:
    """Read a wiki page and return its source_refs slugs."""
    if not page_path.exists():
        return []
    content = page_path.read_text()
    fm = parse_frontmatter(content)
    refs = fm.get("source_refs", [])
    if isinstance(refs, list):
        return [r if isinstance(r, str) else str(r) for r in refs]
    return []


def classify_candidates(
    candidates: list[dict],
    wiki_path: Path,
    manifest: dict,
    recompiled_sources: dict[str, str] | None = None,
) -> dict[str, list]:
    """Classify deduplicated candidates as CREATE, UPDATE, SKIP, or STALE.

    Args:
        candidates: output of deduplicate_candidates
        wiki_path: path to wiki/ directory
        manifest: loaded manifest dict
        recompiled_sources: mapping of source_slug → manifest_key for re-compiled sources

    Returns dict with keys: create, update, skip, stale.
    """
    result = {"create": [], "update": [], "skip": [], "stale": []}

    if not candidates and not recompiled_sources:
        return result

    index_path = wiki_path / "index.md"
    index_content = index_path.read_text() if index_path.exists() else ""
    index_slugs = _parse_index_slugs(index_content)
    alias_map = _build_alias_map(wiki_path)

    candidate_slugs_by_source = {}
    for c in candidates:
        for src in c["sources"]:
            candidate_slugs_by_source.setdefault(src, set()).add(c["slug"])

    for c in candidates:
        slug = c["slug"]
        normalized_name = c["name"].strip().lower()

        existing_slug = None
        existing_category = None
        if slug in index_slugs:
            existing_slug = slug
            existing_category = index_slugs[slug]
        elif normalized_name in alias_map:
            existing_slug = alias_map[normalized_name]
            existing_category = index_slugs.get(existing_slug)

        if existing_slug and existing_category:
            page_path = wiki_path / existing_category / f"{existing_slug}.md"
            existing_refs = _get_existing_source_refs(page_path)
            new_sources = [s for s in c["sources"] if s not in existing_refs]

            if new_sources:
                c["existing_slug"] = existing_slug
                c["existing_category"] = existing_category
                result["update"].append(c)
            else:
                result["skip"].append(c)
        else:
            result["create"].append(c)

    if recompiled_sources:
        for source_slug, manifest_key in recompiled_sources.items():
            entry = manifest.get(manifest_key, {})
            prev_pages = entry.get("wiki_pages", [])
            current_slugs = candidate_slugs_by_source.get(source_slug, set())
            for page_path_str in prev_pages:
                if "/sources/" in page_path_str:
                    continue
                page_slug = Path(page_path_str).stem
                if page_slug not in current_slugs:
                    result["stale"].append({
                        "slug": page_slug,
                        "page": page_path_str,
                        "source": source_slug,
                        "reason": f"absent from re-extraction of {source_slug}",
                    })

    return result
