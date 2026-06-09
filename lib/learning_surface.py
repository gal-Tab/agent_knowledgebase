"""Gating logic for the learn-surface UserPromptSubmit hook — token-frugality core.

Most prompts must inject *nothing*. This module decides, for a given prompt and
the (already-grepped, never-loaded-wholesale) learnings index, whether any past
learning is relevant enough to surface, and if so emits at most three
headline-only lines under a hard token budget.

The bash hook `hooks/learn-surface` is thin glue: it reads the UserPromptSubmit
JSON from stdin, resolves the project + global store indexes, manages the
per-session seen-file, and calls `surface()`. All the decision logic lives here
so it can be unit-tested (mirroring lib/hook_parser + tests/test_hook_status).

Gating rules (locked in the plan):
- A prompt token *hits* a tag when the tag, or any hyphen-part of it, equals a
  prompt token. Each tag contributes at most one hit.
- An entry *qualifies* on >= 2 tag hits, or >= 1 hit if it is a correction
  (corrections are the highest-value learnings — mistakes not to repeat).
- Selection takes <= 3 qualifying entries, corrections first, then by hit count,
  then by recency; ids already surfaced this session are excluded.
"""
from __future__ import annotations

from lib.learning_index import TYPE_CODE, parse_index

# Selection / budget knobs.
MAX_SURFACED = 3
HIT_THRESHOLD = 2          # non-corrections need this many tag hits
CORRECTION_THRESHOLD = 1   # corrections surface on a single hit

# Tokens too generic to carry domain signal — dropped so they never hit a tag.
_STOPWORDS = {
    "how", "the", "and", "for", "you", "are", "was", "this", "that", "what",
    "why", "can", "but", "not", "with", "into", "from", "your", "our", "use",
    "using", "have", "has", "had", "will", "would", "should", "could", "about",
    "when", "where", "which", "they", "them", "then", "than", "want", "need",
}

_MIN_TOKEN_LEN = 3


def extract_tokens(prompt: str) -> set[str]:
    """Lowercase the prompt, split on non-alphanumerics, drop short/stop tokens."""
    if not prompt:
        return set()
    tokens: set[str] = set()
    word = []
    for ch in prompt.lower():
        if ch.isalnum():
            word.append(ch)
        elif word:
            tokens.add("".join(word))
            word = []
    if word:
        tokens.add("".join(word))
    return {
        t for t in tokens
        if len(t) >= _MIN_TOKEN_LEN and t not in _STOPWORDS
    }


def count_tag_hits(tags: list[str], tokens: set[str]) -> int:
    """How many of `tags` are matched by the prompt `tokens`.

    A tag matches on an exact token match, or when any of its hyphen-separated
    parts matches a token. Each tag counts at most once.
    """
    hits = 0
    for tag in tags:
        tag = tag.lower()
        parts = [p for p in tag.split("-") if p]
        if tag in tokens or any(p in tokens for p in parts):
            hits += 1
    return hits


def qualifies(entry_type: str, hits: int) -> bool:
    """Whether an entry with `hits` tag hits clears the gating threshold."""
    if hits <= 0:
        return False
    threshold = CORRECTION_THRESHOLD if entry_type == "correction" else HIT_THRESHOLD
    return hits >= threshold


def select(entries: list[dict], prompt: str, seen_ids=None, limit: int = MAX_SURFACED) -> list[dict]:
    """Pick the entries to surface for `prompt`, highest-value first.

    Corrections rank ahead of everything else; within a rank, more tag hits and
    then more recent dates win. Entries in `seen_ids` (already surfaced this
    session) are skipped, as are entries below threshold.
    """
    seen_ids = seen_ids or set()
    tokens = extract_tokens(prompt)

    scored = []
    for e in entries:
        if e.get("id") in seen_ids:
            continue
        hits = count_tag_hits(e.get("tags") or [], tokens)
        if not qualifies(e.get("type"), hits):
            continue
        scored.append((e, hits))

    scored.sort(
        key=lambda pair: (
            0 if pair[0].get("type") == "correction" else 1,  # corrections first
            -pair[1],                                          # more hits first
            _date_sort_key(pair[0].get("date", "")),           # recent first
        )
    )
    return [e for e, _ in scored[:limit]]


def _date_sort_key(date: str) -> str:
    """Sort key that puts more-recent ISO dates first under ascending sort."""
    # Invert each char so a plain ascending sort yields descending dates without
    # needing reverse= (which would fight the other ascending keys in the tuple).
    return "".join(chr(255 - ord(c)) for c in date)


def render(entries: list[dict]) -> str:
    """Render selected entries as a lean, headline-only block (or "" if none).

    Headline-only by design: a type code + the (<=100 char) headline per line,
    one short pointer line. With at most three lines this stays near the
    ~70-90 token budget; the body is fetched on demand via /learn-recall.
    """
    if not entries:
        return ""
    lines = ["Relevant past learnings (from compound-knowledge):"]
    for e in entries:
        code = TYPE_CODE.get(e.get("type"), "?")
        lines.append(f"- [{code}] {e.get('headline', '').strip()}")
    lines.append("→ /learn-recall (or read the learnings index) for full text + ids.")
    return "\n".join(lines)


def surface(index_texts: list[str], prompt: str, seen_ids=None):
    """Top-level decision for the hook.

    `index_texts` are the raw index.md texts of the resolved stores, project
    first then global. Returns `(output_text, surfaced_ids)`:
    output is "" when nothing qualifies (the common case), and surfaced_ids
    lists the ids that were emitted so the caller can record them for
    per-session dedup.
    """
    seen_ids = seen_ids or set()

    # Merge tiers, project shadowing global on id collision.
    merged: list[dict] = []
    seen_merge = set()
    for text in index_texts:
        for entry in parse_index(text):
            if entry["id"] in seen_merge:
                continue
            seen_merge.add(entry["id"])
            merged.append(entry)

    chosen = select(merged, prompt, seen_ids=seen_ids)
    if not chosen:
        return "", []
    return render(chosen), [e["id"] for e in chosen]
