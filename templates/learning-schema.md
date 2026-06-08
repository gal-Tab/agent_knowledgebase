# Learning Schema

The canonical contract for **compound learnings** — the agent's own work-lessons,
distinct from the source-document wiki (see `wiki-schema.md`). This file is the
human-readable spec; `lib/learning_format.py` is its executable enforcement.

## What a learning is (and isn't)

A learning captures something the agent should *do differently or remember* on
future work, in any project. It is **not** a summary of an external source
(that's a wiki `source` page) and **not** a user preference or behavior
("the user likes concise prose") — those belong in the MEMORY system, not here.

## Stores (two tiers)

- **Project** (primary): `.compound/` in the repo — committed, team-shareable.
  This is the default scope for every capture.
- **Global** (opt-in, curated): `~/.claude/compound-knowledge/` (override with
  `$COMPOUND_KNOWLEDGE_HOME`) — cross-project, personal, git-init'd. A learning
  is promoted here **only** when it generalizes beyond the current repo, with
  explicit approval. It is never a dump of every session.

Layout (identical per tier): `<root>/{insights,playbooks,corrections,patterns}/<id>.md`,
plus `.archive/` (superseded) and `.drafts/` (pending approval). The retrieval
index is `<root>/index.md`.

## Types

| type | when |
|------|------|
| **correction** | A mistake we made / a thing not to do. Highest-value — surfaced first. |
| **playbook** | A repeatable process or sequence that worked. |
| **insight** | New understanding about a problem or domain. |
| **pattern** | An observation about how something behaves/recurs. |

## Frontmatter

```yaml
id: kw-YYYY-MM-DD-<slug>      # stable, unique; slug derived from headline
type: correction              # insight | playbook | correction | pattern
scope: project                # project (default) | global (set on promotion)
headline: ""                  # <= 100 chars — this is the index line; make it self-contained
tags: [lowercased, hyphenated]# drive gated retrieval; choose terms a future search would use
confidence: STATED            # STATED | INFERRED | UNCERTAIN
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active                # active | archived | superseded
supersedes: []                # ids this learning replaces (optional)
superseded_by: null           # id that replaced this (set on archival)
```

Required: `id, type, headline, tags, confidence, created, updated, status`.

## Sections

```markdown
## Learning
1–3 sentences: the durable lesson, stated plainly.

## Context
When/where it applies — the trigger conditions. Keeps retrieval precise.

## Implication
What to do differently next time. For playbooks, the concrete steps.
```

## Confidence

- **STATED** — directly observed/verified this session.
- **INFERRED** — a reasonable deduction, not directly confirmed.
- **UNCERTAIN** — flagged for review; weak or conflicting evidence.

Mark a single-data-point lesson `UNCERTAIN` or `INFERRED`; reserve `STATED` for
verified lessons.

## Rules

- **1–3 learnings max per capture.** Quality over quantity — vague learnings are useless.
- **Approval always required.** Never auto-save; never silent-write.
- **Project scope by default.** Promote to global only when genuinely generalizable.
- **Corrections always win.** A correction that contradicts an older learning
  supersedes it (the old one is archived, not deleted).
