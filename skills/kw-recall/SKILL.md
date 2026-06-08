---
name: kw-recall
description: Use when the user asks what was learned before, references past mistakes/lessons/playbooks ("have we hit this before", "what did we learn about X", "lessons learned", "did I already solve this"), or when you want to consult the agent's own compound learnings before acting. Reads the compound-learnings store (project .compound/ + the global store), index-first.
allowed-tools: Read, Glob, Grep
---

# Compound Learnings — Recall

Consult the agent's own accumulated **work-lessons** (corrections, playbooks,
insights, patterns) to answer "have we learned this before?" and to inform how
you approach the current task. These are the agent's lessons — **not** source
wiki pages (`kb-query` handles those) and **not** user preferences (those live
in MEMORY).

This skill is **index-first and token-frugal**: read the compact index, then
fetch at most a handful of bodies, and only the ones that actually sharpen the
answer. Never load the store wholesale.

## When to Use This Skill

- User asks what was learned/decided before, or references past mistakes,
  corrections, playbooks, or "lessons learned."
- User asks "have we hit this before?", "did I already solve this?", "what's our
  approach to X?"
- You are about to start a task and want to check for a relevant past correction
  or blessed playbook before acting.

## When NOT to Use This Skill

- Domain questions about ingested sources → use `kb-query` (the wiki).
- User *preferences/behaviors* → those are MEMORY, not learnings.
- Capturing a new lesson → use `/kw-compound`. This skill is read-only.
- General coding questions with no relevant captured learning.

## The Two Stores

Retrieval merges both tiers; the **project store shadows global** on id collision.

| Scope | Root | Notes |
|-------|------|-------|
| project | `<repo>/.compound/` | primary, committed, team-shared |
| global | `$COMPOUND_KNOWLEDGE_HOME` or `~/.claude/compound-knowledge/` | opt-in, curated, cross-project |

Each store: a compact `index.md` plus per-type bodies under
`insights/ playbooks/ corrections/ patterns/`. The index line schema is:

```
- [CODE] {id} | {tags} | {headline} | {confidence} | {date}
```

Type codes → body directory: `C` → `corrections/`, `P` → `playbooks/`,
`I` → `insights/`, `Pa` → `patterns/`. The body file is `<root>/<dir>/<id>.md`.

## Recall Procedure

1. **Locate the indexes.** Read `<repo>/.compound/index.md` and the global
   `index.md` (under `$COMPOUND_KNOWLEDGE_HOME` or `~/.claude/compound-knowledge/`).
   If neither exists, say no learnings have been captured yet and stop — there is
   nothing to recall.

2. **Scan the index lines** (cheap — they are headline-only). Match the user's
   question against the **tags** column and headlines. If a store is large, use
   `grep -i "<term>" <root>/index.md` to find candidate lines rather than reading
   the whole file. **Corrections rank first** (mistakes not to repeat), then
   playbooks, then insights/patterns.

3. **Merge tiers**, project over global on duplicate id. Keep the most relevant
   candidates (typically ≤5).

4. **Fetch bodies on demand — at most 5, only when needed.** For a candidate that
   directly answers the question, read its body at `<root>/<type-dir>/<id>.md`
   (or `Glob` for `**/<id>.md` if unsure of the type). Skip bodies whose headline
   already answers the question — many recalls need no body read at all.

5. **Synthesize and cite ids and scope.** Lead with corrections. For each lesson
   used, cite its id and scope, e.g.:
   - "A past correction (`kw-2026-06-08-retry-jitter`, project) says: add jitter…"
   - "Per the blessed playbook `kw-…-deploy` (global): …"
   Distinguish a captured learning from general reasoning when you add your own.

## Guardrails

- **Index-first, never load the store wholesale.** Read indexes, then bodies on
  demand.
- **At most 5 bodies per recall** unless the user explicitly asks for a full
  review.
- **Read-only.** This skill never writes, edits, or archives. To capture or
  update a lesson, route to `/kw-compound`.
- **Cite ids + scope** for every lesson you rely on.
- **Corrections first** — surface contradicting/cautionary lessons before
  reinforcing ones.
