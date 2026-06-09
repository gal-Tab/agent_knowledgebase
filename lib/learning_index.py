"""Compact index for compound learnings — the token-frugality core.

The index is one greppable line per active learning, bucketed by type with
corrections first. Retrieval (the learn-surface hook, learn-recall, learn-research,
and wiki-query) greps THIS file and reads bodies only on demand — it never loads
the store wholesale. At thousands of learnings the index is still a single
small file read by grep, not by the model.

Line format:
    - [CODE] {id} | {tags csv} | {headline} | {confidence} | {date}

Type codes: insight=I, playbook=P, correction=C, pattern=Pa.
Archived and draft learnings are excluded (they cost zero retrieval tokens).
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from lib.page_format import parse_frontmatter

# type → (single-line code, header label suffix, bucket order)
TYPE_CODE = {"insight": "I", "playbook": "P", "correction": "C", "pattern": "Pa"}
CODE_TYPE = {v: k for k, v in TYPE_CODE.items()}

# Buckets render in this order — corrections first so a budgeted reader hits
# the highest-value learnings (mistakes not to repeat) by position.
BUCKET_ORDER = ["correction", "playbook", "insight", "pattern"]
BUCKET_HEADING = {
    "correction": "## corrections",
    "playbook": "## playbooks",
    "insight": "## insights",
    "pattern": "## patterns",
}

_LINE_RE = re.compile(
    r"^- \[(?P<code>\w+)\] (?P<id>\S+) \| (?P<tags>.*?) \| (?P<headline>.*?) \| "
    r"(?P<confidence>\w+) \| (?P<date>\S+)\s*$"
)
_ARCHIVED_RE = re.compile(r"Archived:\s*(\d+)")


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _sanitize(text: str) -> str:
    """Keep a field single-line and pipe-free so the line schema stays parseable."""
    return str(text).replace("|", "/").replace("\n", " ").strip()


def format_line(entry: dict) -> str:
    """Render one index line from an entry dict."""
    code = TYPE_CODE.get(entry["type"], "?")
    tags = ",".join(entry.get("tags") or [])
    return (
        f"- [{code}] {entry['id']} | {_sanitize(tags)} | {_sanitize(entry['headline'])} | "
        f"{entry['confidence']} | {entry['date']}"
    )


def parse_line(line: str) -> dict | None:
    """Parse one index line into an entry dict, or None if it is not a learning line."""
    m = _LINE_RE.match(line.rstrip())
    if not m:
        return None
    tags = [t.strip() for t in m["tags"].split(",") if t.strip()]
    return {
        "type": CODE_TYPE.get(m["code"], m["code"]),
        "id": m["id"],
        "tags": tags,
        "headline": m["headline"].strip(),
        "confidence": m["confidence"],
        "date": m["date"],
    }


def entry_from_content(content: str) -> dict:
    """Build an index entry from a learning file's frontmatter."""
    fm = parse_frontmatter(content)
    return {
        "type": fm.get("type"),
        "id": fm.get("id"),
        "tags": fm.get("tags") or [],
        "headline": fm.get("headline", ""),
        "confidence": fm.get("confidence", ""),
        "date": str(fm.get("updated") or fm.get("created") or ""),
        "status": fm.get("status", "active"),
    }


def parse_index(text: str) -> list[dict]:
    """Parse all learning lines out of an index.md text."""
    return [e for e in (parse_line(line) for line in text.splitlines()) if e]


def parse_archived_count(text: str) -> int:
    """Read the 'Archived: N' figure from an index header (0 if absent)."""
    m = _ARCHIVED_RE.search(text)
    return int(m.group(1)) if m else 0


def build_index(entries: list[dict], updated: str | None = None, archived: int = 0) -> str:
    """Render the full index.md text from a list of entries.

    Entries are grouped into type buckets (corrections first) and sorted by
    date descending within each bucket. Only buckets with entries are emitted.
    """
    updated = updated or _today()
    counts = {t: 0 for t in TYPE_CODE}
    for e in entries:
        if e.get("type") in counts:
            counts[e["type"]] += 1
    total = sum(counts.values())

    header = (
        "# Compound Learnings Index\n"
        f"Updated: {updated} | Total: {total} "
        f"({counts['insight']}i/{counts['playbook']}p/{counts['correction']}c/{counts['pattern']}pa) "
        f"| Archived: {archived}\n"
    )

    parts = [header]
    for bucket in BUCKET_ORDER:
        bucket_entries = [e for e in entries if e.get("type") == bucket]
        if not bucket_entries:
            continue
        bucket_entries.sort(key=lambda e: e.get("date", ""), reverse=True)
        parts.append("\n" + BUCKET_HEADING[bucket] + "\n")
        parts.extend(format_line(e) + "\n" for e in bucket_entries)

    return "".join(parts)


def scan_store(root: Path | str) -> list[dict]:
    """Scan a store root for ACTIVE learnings and return index entries.

    Walks only the per-type directories — `.archive/` and `.drafts/` live
    outside them and are therefore excluded by construction. Learnings whose
    status is not 'active' are also dropped.
    """
    from lib.learning_store import TYPE_DIRS

    root = Path(root)
    entries: list[dict] = []
    for type_dir in TYPE_DIRS.values():
        d = root / type_dir
        if not d.exists():
            continue
        for md in sorted(d.glob("*.md")):
            entry = entry_from_content(md.read_text())
            if entry.get("status", "active") == "active":
                entries.append(entry)
    return entries


def count_archived(root: Path | str) -> int:
    """Count archived learnings under a store's .archive/ (md files only)."""
    from lib.learning_store import ARCHIVE_DIRNAME

    adir = Path(root) / ARCHIVE_DIRNAME
    if not adir.exists():
        return 0
    return sum(1 for _ in adir.rglob("*.md"))


def append_entry(index_path: Path | str, entry: dict, updated: str | None = None) -> str:
    """Add or update a single entry in an index file (reads the index, not the store).

    This is the O(cheap) common path used on promotion: it parses the existing
    index lines, replaces any line with the same id, appends the new entry, and
    re-renders. It does NOT scan learning bodies — that is `rebuild`'s job.
    """
    index_path = Path(index_path)
    if index_path.exists():
        text = index_path.read_text()
        entries = parse_index(text)
        archived = parse_archived_count(text)
    else:
        entries, archived = [], 0

    entries = [e for e in entries if e["id"] != entry["id"]]
    entries.append(
        {k: entry[k] for k in ("type", "id", "tags", "headline", "confidence", "date")}
    )

    new_text = build_index(entries, updated=updated, archived=archived)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(new_text)
    return new_text


def rebuild(root: Path | str, updated: str | None = None) -> str:
    """Full rebuild: scan the store, recount archived, write root/index.md."""
    root = Path(root)
    entries = scan_store(root)
    archived = count_archived(root)
    text = build_index(entries, updated=updated, archived=archived)
    root.mkdir(parents=True, exist_ok=True)
    (root / "index.md").write_text(text)
    return text
