#!/usr/bin/env python3
"""Generate a Mermaid relationship graph from wiki pages.

Reads wiki/index.md and page frontmatter (source_refs, key_entities, key_concepts)
to build a graph showing entity↔source↔concept relationships.

Usage: generate-graph.py [wiki_dir] [output_file]
  Defaults: wiki_dir=wiki, output_file=wiki/graph.mmd
"""
import os
import re
import sys
from pathlib import Path


def parse_frontmatter(content: str) -> dict:
    """Simple YAML frontmatter parser."""
    if not content.startswith("---"):
        return {}
    end = content.find("---", 3)
    if end == -1:
        return {}
    fm_text = content[3:end].strip()
    result = {}
    current_key = None
    current_list = None
    for line in fm_text.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- ") and current_key is not None:
            if current_list is None:
                current_list = []
                result[current_key] = current_list
            value = stripped[2:].strip().strip('"').strip("'")
            current_list.append(value)
            continue
        if ":" in stripped:
            current_list = None
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            current_key = key
            if value == "[]":
                result[key] = []
            elif value:
                result[key] = value
            else:
                result[key] = ""
    return result


def sanitize_id(slug: str) -> str:
    """Make a slug safe for Mermaid node IDs."""
    return re.sub(r"[^a-zA-Z0-9]", "_", slug)


def read_wiki_pages(wiki_dir: str) -> list[dict]:
    """Read all wiki pages and extract metadata."""
    pages = []
    for category in ("sources", "entities", "concepts", "comparisons"):
        cat_dir = os.path.join(wiki_dir, category)
        if not os.path.isdir(cat_dir):
            continue
        for filename in os.listdir(cat_dir):
            if not filename.endswith(".md") or filename.startswith("_"):
                continue
            filepath = os.path.join(cat_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            fm = parse_frontmatter(content)
            slug = filename[:-3]  # remove .md
            pages.append({
                "slug": slug,
                "title": fm.get("title", slug),
                "type": fm.get("type", category.rstrip("s")),
                "category": category,
                "key_entities": fm.get("key_entities", []),
                "key_concepts": fm.get("key_concepts", []),
                "source_refs": fm.get("source_refs", []),
            })
    return pages


def generate_mermaid(pages: list[dict]) -> str:
    """Generate Mermaid graph definition from wiki pages."""
    lines = ["graph LR"]
    lines.append("")

    # Group pages by type for styling
    sources = [p for p in pages if p["category"] == "sources"]
    entities = [p for p in pages if p["category"] == "entities"]
    concepts = [p for p in pages if p["category"] == "concepts"]

    # Prefix node IDs with category to avoid collisions
    # (e.g., source "attention-mechanisms" vs concept "attention-mechanisms")
    def node_id(category: str, slug: str) -> str:
        prefix = category[0]  # s, e, c
        return f"{prefix}_{sanitize_id(slug)}"

    # Define nodes with shapes
    lines.append("    %% Sources (rectangles)")
    for p in sources:
        nid = node_id("s", p["slug"])
        label = p["title"][:40] + ("..." if len(p["title"]) > 40 else "")
        lines.append(f'    {nid}["{label}"]')

    lines.append("")
    lines.append("    %% Entities (rounded rectangles)")
    for p in entities:
        nid = node_id("e", p["slug"])
        label = p["title"]
        lines.append(f'    {nid}("{label}")')

    lines.append("")
    lines.append("    %% Concepts (hexagons)")
    for p in concepts:
        nid = node_id("c", p["slug"])
        label = p["title"]
        lines.append(f'    {nid}{{{{{label}}}}}')

    lines.append("")
    lines.append("    %% Relationships")

    # Build lookup for entity/concept slugs
    entity_slugs = {p["slug"] for p in entities}
    concept_slugs = {p["slug"] for p in concepts}

    # Build edges from source → entity and source → concept (via key_entities/key_concepts)
    seen_edges = set()
    for p in sources:
        src_nid = node_id("s", p["slug"])
        for entity_slug in (p.get("key_entities") or []):
            if isinstance(entity_slug, str) and entity_slug in entity_slugs:
                ent_nid = node_id("e", entity_slug)
                edge = (src_nid, ent_nid)
                if edge not in seen_edges:
                    lines.append(f"    {src_nid} --> {ent_nid}")
                    seen_edges.add(edge)

        for concept_slug in (p.get("key_concepts") or []):
            if isinstance(concept_slug, str) and concept_slug in concept_slugs:
                con_nid = node_id("c", concept_slug)
                edge = (src_nid, con_nid)
                if edge not in seen_edges:
                    lines.append(f"    {src_nid} -.-> {con_nid}")
                    seen_edges.add(edge)

    lines.append("")
    lines.append("    %% Styling")
    lines.append("    classDef source fill:#4a90d9,stroke:#2c5f8a,color:#fff")
    lines.append("    classDef entity fill:#50c878,stroke:#2e8b57,color:#fff")
    lines.append("    classDef concept fill:#daa520,stroke:#b8860b,color:#fff")

    if sources:
        ids = ",".join(node_id("s", p["slug"]) for p in sources)
        lines.append(f"    class {ids} source")
    if entities:
        ids = ",".join(node_id("e", p["slug"]) for p in entities)
        lines.append(f"    class {ids} entity")
    if concepts:
        ids = ",".join(node_id("c", p["slug"]) for p in concepts)
        lines.append(f"    class {ids} concept")

    return "\n".join(lines) + "\n"


def main():
    wiki_dir = sys.argv[1] if len(sys.argv) > 1 else "wiki"
    output_file = sys.argv[2] if len(sys.argv) > 2 else os.path.join(wiki_dir, "graph.mmd")

    if not os.path.isdir(wiki_dir):
        print(f"Error: wiki directory '{wiki_dir}' not found", file=sys.stderr)
        sys.exit(1)

    pages = read_wiki_pages(wiki_dir)
    if not pages:
        print("No wiki pages found.", file=sys.stderr)
        sys.exit(1)

    mermaid = generate_mermaid(pages)

    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(mermaid)

    print(f"Generated {output_file} with {len(pages)} nodes")


if __name__ == "__main__":
    main()
