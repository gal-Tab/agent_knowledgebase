"""Dedup-on-write resolution for compound learnings (the kw-* subsystem).

Mirrors tools/resolve_candidates.py for the learnings store: given a candidate
learning and the existing (active) index entries, classify the write as

    CREATE    — no matching learning, file it fresh
    UPDATE    — same topic + same type already exists, refine it in place
    SKIP      — an identical learning already exists, do nothing
    SUPERSEDE — this contradicts an active learning; archive the old one

"Corrections always win": a correction on the same topic as an active
non-correction supersedes it (even without an explicit `supersedes:` list), and
an explicit `supersedes: [id]` always supersedes. `supersede()` performs the
side effect — it stamps the old learning `status: superseded` /
`superseded_by`, archives it (lib.learning_store.move_to_archive), and rebuilds
the index so the superseded learning drops out of active retrieval.

Topic identity is the slug component of the id (`kw-YYYY-MM-DD-<slug>`), so the
same lesson recaptured on a later date resolves against the earlier one.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.learning_index import parse_index, rebuild
from lib.learning_store import TYPE_DIRS, move_to_archive
from lib.page_format import parse_frontmatter
from lib.slug import slug_learning

CREATE = "CREATE"
UPDATE = "UPDATE"
SKIP = "SKIP"
SUPERSEDE = "SUPERSEDE"

_ID_SLUG_RE = re.compile(r"^kw-\d{4}-\d{2}-\d{2}-(?P<slug>.+)$")


def topic_key(value: str) -> str:
    """The topic identity of a learning: the slug of its id or headline.

    Accepts either a full id (`kw-YYYY-MM-DD-<slug>`) — returning <slug> — or a
    raw headline, which is slugified. The same lesson captured on different days
    yields the same key, so recaptures resolve against the original.
    """
    if not value:
        return ""
    m = _ID_SLUG_RE.match(value.strip())
    if m:
        return m.group("slug")
    return slug_learning(value)


def _norm_tags(tags) -> set[str]:
    return {str(t).strip().lower() for t in (tags or []) if str(t).strip()}


def _candidate_key(candidate: dict) -> str:
    return topic_key(candidate.get("id") or candidate.get("headline", ""))


def _resolution(action, candidate, target_id=None, superseded_ids=None):
    return {
        "action": action,
        "candidate": candidate,
        "target_id": target_id,
        "superseded_ids": superseded_ids or [],
    }


def classify_learning(candidate: dict, existing: list[dict]) -> dict:
    """Classify how a candidate learning should be written against `existing`.

    `candidate` needs at least `type`, `headline`, `tags`; `id` and `supersedes`
    are optional. `existing` are active index entries (parse_index output).
    Returns a resolution dict: {action, candidate, target_id, superseded_ids}.
    """
    ckey = _candidate_key(candidate)
    ctype = candidate.get("type")
    existing_by_id = {e["id"]: e for e in existing}

    # Explicit supersession always wins — but only for targets that actually exist.
    explicit = [sid for sid in (candidate.get("supersedes") or []) if sid in existing_by_id]
    if explicit:
        return _resolution(SUPERSEDE, candidate, superseded_ids=explicit)

    same_topic = [e for e in existing if topic_key(e["id"]) == ckey]
    same_type_topic = [e for e in same_topic if e.get("type") == ctype]

    # Dedup within the same type/topic first (so a correction never supersedes
    # an existing correction about the same thing — it refines it instead).
    if same_type_topic:
        e = same_type_topic[0]
        identical = (
            e.get("headline", "").strip() == candidate.get("headline", "").strip()
            and _norm_tags(e.get("tags")) == _norm_tags(candidate.get("tags"))
        )
        return _resolution(SKIP if identical else UPDATE, candidate, target_id=e["id"])

    # Corrections always win: contradict an active non-correction on the same topic.
    if ctype == "correction":
        targets = [e["id"] for e in same_topic if e.get("type") != "correction"]
        if targets:
            return _resolution(SUPERSEDE, candidate, superseded_ids=targets)

    return _resolution(CREATE, candidate)


def classify_batch(candidates: list[dict], existing: list[dict]) -> list[dict]:
    """Classify several candidates against the same existing index (no I/O)."""
    return [classify_learning(c, existing) for c in candidates]


def format_brief(resolutions: list[dict]) -> str:
    """Render actionable resolutions as a markdown brief (SKIPs omitted)."""
    buckets = {CREATE: [], UPDATE: [], SUPERSEDE: []}
    for r in resolutions:
        if r["action"] in buckets:
            buckets[r["action"]].append(r)

    if not any(buckets.values()):
        return ""

    lines: list[str] = []
    for action in (SUPERSEDE, UPDATE, CREATE):  # highest-impact first
        rs = buckets[action]
        if not rs:
            continue
        lines.append(f"## {action} ({len(rs)})\n")
        for r in rs:
            c = r["candidate"]
            label = f"[{c.get('type', '?')}] {c.get('headline', '')}"
            if action == SUPERSEDE:
                lines.append(f"- {label} — supersedes {', '.join(r['superseded_ids'])}")
            elif action == UPDATE:
                lines.append(f"- {label} — updates {r['target_id']}")
            else:
                lines.append(f"- {label}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _find_learning(root: Path, lid: str) -> tuple[str, Path]:
    """Locate an active learning by id; return (type, path). Raise if absent."""
    root = Path(root)
    for ltype, dirname in TYPE_DIRS.items():
        path = root / dirname / f"{lid}.md"
        if path.exists():
            return ltype, path
    raise FileNotFoundError(f"no active learning '{lid}' under {root}")


def supersede(root: Path | str, superseded_id: str, new_id: str, reason: str) -> Path:
    """Archive a superseded learning and drop it from the active index.

    Stamps the old learning `status: superseded` and `superseded_by: <new_id>`,
    moves it to `.archive/` with a JSON sidecar (archive, never delete), then
    rebuilds the index so it no longer surfaces. Returns the archive path.
    """
    root = Path(root)
    ltype, path = _find_learning(root, superseded_id)

    content = path.read_text()
    content = re.sub(r"(?m)^status:.*$", "status: superseded", content, count=1)
    content = re.sub(
        r"(?m)^superseded_by:.*$", f"superseded_by: {new_id}", content, count=1
    )
    path.write_text(content)

    archive_path = move_to_archive(root, ltype, superseded_id, reason, superseded_by=new_id)
    rebuild(root)
    return archive_path


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Classify a candidate learning (dedup-on-write) against a store."
    )
    parser.add_argument("draft", type=Path, help="Path to the candidate learning markdown")
    parser.add_argument("--root", type=Path, required=True, help="Store root (e.g. .compound)")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Perform supersession side effects (archive + index rebuild). "
        "Default is dry-run: classify and print the brief only.",
    )
    args = parser.parse_args()

    candidate = parse_frontmatter(args.draft.read_text())
    index_path = args.root / "index.md"
    existing = parse_index(index_path.read_text()) if index_path.exists() else []

    resolution = classify_learning(candidate, existing)
    brief = format_brief([resolution])
    print(brief or f"SKIP — {candidate.get('headline', '')} already captured.\n", end="")

    if args.apply and resolution["action"] == SUPERSEDE:
        for old_id in resolution["superseded_ids"]:
            arch = supersede(
                args.root, old_id, candidate["id"], reason="contradicted by new learning"
            )
            print(f"archived {old_id} -> {arch}")


if __name__ == "__main__":
    main()
