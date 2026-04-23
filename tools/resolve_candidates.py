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


def format_brief(classified: dict) -> str:
    """Format classified candidates as a markdown resolution brief.

    SKIPs are omitted. Returns empty string if nothing to resolve.
    """
    sections = []
    creates = classified["create"]
    updates = classified["update"]
    stales = classified["stale"]

    if not creates and not updates and not stales:
        return ""

    if creates:
        sections.append(f"## CREATE ({len(creates)})\n")
        for c in creates:
            kind_label = c["kind"].capitalize()
            type_info = f" ({c.get('entity_type', '')})" if c.get("entity_type") else ""
            sections.append(f"### {kind_label}: {c['name']}{type_info} → {c['slug']}")
            for src, desc in c.get("descriptions", {}).items():
                sections.append(f"- {src}: {desc}")
            sections.append("")

    if updates:
        sections.append(f"## UPDATE ({len(updates)})\n")
        for c in updates:
            kind_label = c["kind"].capitalize()
            type_info = f" ({c.get('entity_type', '')})" if c.get("entity_type") else ""
            existing = c.get("existing_slug", c["slug"])
            sources_str = ", ".join(c["sources"])
            sections.append(f"### {kind_label}: {c['name']}{type_info} → {existing}")
            sections.append(f"Sources adding: {sources_str}")
            for src, desc in c.get("descriptions", {}).items():
                sections.append(f"- {src}: {desc}")
            sections.append("")

    if stales:
        sections.append(f"## STALE ({len(stales)})\n")
        for s in stales:
            sections.append(f"- {s['slug']} ({s['page']}) — {s['reason']}")
        sections.append("")

    return "\n".join(sections).strip() + "\n"


def batch_candidates(
    classified: dict,
    max_sources: int = 5,
    max_candidates: int = 30,
) -> list[dict]:
    """Split classified candidates into batches respecting limits.

    Splits at source boundaries. STALE entries go in first batch only.
    """
    creates = classified["create"]
    updates = classified["update"]
    stales = classified["stale"]
    all_actionable = creates + updates

    if len(all_actionable) <= max_candidates:
        return [classified]

    by_source = {}
    for c in all_actionable:
        for src in c.get("sources", []):
            by_source.setdefault(src, []).append(c)

    batches = []
    current_batch = {"create": [], "update": [], "skip": [], "stale": []}
    current_count = 0
    current_sources = 0
    seen_slugs = set()

    for src, src_candidates in by_source.items():
        src_new = [c for c in src_candidates if c["slug"] not in seen_slugs]
        if not src_new:
            continue

        would_exceed = (
            current_count + len(src_new) > max_candidates
            or current_sources + 1 > max_sources
        )
        if would_exceed and current_count > 0:
            batches.append(current_batch)
            current_batch = {"create": [], "update": [], "skip": [], "stale": []}
            current_count = 0
            current_sources = 0

        for c in src_new:
            if c["slug"] in seen_slugs:
                continue
            seen_slugs.add(c["slug"])
            bucket = "update" if "existing_slug" in c else "create"
            current_batch[bucket].append(c)
            current_count += 1
        current_sources += 1

    if current_count > 0:
        batches.append(current_batch)

    if batches and stales:
        batches[0]["stale"] = stales

    return batches if batches else [classified]


def main():
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Batch resolution candidate collector")
    parser.add_argument("wiki_path", type=Path, help="Path to wiki/ directory")
    parser.add_argument("results_path", type=Path, help="Path to raw/.compile-results/")
    parser.add_argument("manifest_path", type=Path, help="Path to raw/.manifest.json")
    parser.add_argument("--batch-size", type=int, default=5, help="Max sources per batch")
    parser.add_argument("--max-candidates", type=int, default=30, help="Max candidates per batch")
    args = parser.parse_args()

    manifest = {}
    if args.manifest_path.exists():
        manifest = json.loads(args.manifest_path.read_text())

    result_files = sorted(args.results_path.glob("*.json"))
    all_candidates = []
    recompiled = {}

    for rf in result_files:
        result = json.loads(rf.read_text())
        if result.get("status") != "success":
            continue
        slug = result["slug"]
        source_page = args.wiki_path / "sources" / f"{slug}.md"
        if not source_page.exists():
            continue
        content = source_page.read_text()
        parsed = parse_extracted_references(content, slug)
        all_candidates.extend(parsed)

        source_file = result.get("source_file", "")
        if source_file in manifest and manifest[source_file].get("status") == "compiled":
            recompiled[slug] = source_file

    if not all_candidates and not recompiled:
        return

    deduped = deduplicate_candidates(all_candidates)
    classified = classify_candidates(deduped, args.wiki_path, manifest, recompiled or None)

    batches = batch_candidates(classified, args.batch_size, args.max_candidates)

    for i, batch in enumerate(batches):
        if i > 0:
            print("\n---BATCH---\n")
        brief = format_brief(batch)
        if brief:
            print(brief, end="")


if __name__ == "__main__":
    main()
