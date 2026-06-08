---
name: kw-researcher
description: Use when planning or brainstorming a non-trivial task and you want a thorough, one-shot sweep of the agent's past learnings before committing to an approach — best run as a dispatched subagent so the scan happens in its own token budget and returns only a synthesized, cited brief. Read-only. For quick interactive lookups during a conversation, use kw-recall instead.
allowed-tools: Read, Glob, Grep
---

# Compound Learnings — Researcher (planning subagent)

Sweep the compound-learnings store at **planning time** and return a short,
cited brief of the lessons that bear on the task at hand — past corrections to
respect, playbooks to reuse, insights/patterns to factor in. This is the
heavier, comprehensive counterpart to `kw-recall`.

**Run this as a dispatched subagent.** The point is isolation: the subagent does
the grepping and body-reading in *its own* context budget and hands back only the
synthesized findings, so the planner's context stays lean. It is **read-only** —
it never writes, edits, archives, or captures.

## When to Use This Skill

- You are about to plan or brainstorm a feature, migration, or fix and want to
  front-load relevant past lessons.
- A planning step asks "what have we learned that applies here?" across a broad
  topic, where a single interactive lookup would be too shallow.

## When NOT to Use This Skill

- Quick, in-conversation recall → use **`kw-recall`** (inline, cheaper).
- Domain questions about ingested sources → `kb-query`.
- Capturing or updating a lesson → `/kw-compound`. This skill never writes.
- No store exists → there is nothing to research; say so and stop.

## The Two Stores

Merge both tiers; **project shadows global** on id collision.

| Scope | Root |
|-------|------|
| project | `<repo>/.compound/` |
| global | `$COMPOUND_KNOWLEDGE_HOME` or `~/.claude/compound-knowledge/` |

Each store: a compact `index.md` plus per-type bodies under
`insights/ playbooks/ corrections/ patterns/`. Index line schema:
`- [CODE] {id} | {tags} | {headline} | {confidence} | {date}`.
Type codes → dirs: `C`→`corrections/`, `P`→`playbooks/`, `I`→`insights/`, `Pa`→`patterns/`.

## Research Procedure

1. **Derive search terms** from the task: key nouns, tools, error classes,
   domains. Lowercase/hyphenate to match the tag column.

2. **Grep both indexes, never load them whole.** For each term:

   ```bash
   grep -i "<term>" .compound/index.md "$COMPOUND_KNOWLEDGE_HOME/index.md" ~/.claude/compound-knowledge/index.md 2>/dev/null
   ```

   If neither index exists, report "no learnings captured" and stop.

3. **Rank candidates.** Merge tiers (project over global). Order **corrections
   first** (mistakes not to repeat), then playbooks, then insights/patterns; break
   ties by tag-overlap with the task and recency.

4. **Read bodies on demand, capped.** Read at most **~7** bodies
   (`<root>/<type-dir>/<id>.md`), prioritising the top-ranked. Skip any whose
   headline already tells you what you need. Log if you hit the cap so the planner
   knows coverage was bounded.

5. **Return a synthesized, cited brief — findings only.** Do not dump file
   contents. Structure it as:
   - **Corrections to respect** — `id` (scope): the lesson + how it constrains the plan.
   - **Playbooks to reuse** — `id` (scope): the procedure + when it applies.
   - **Insights/patterns** — `id` (scope): the relevant takeaway.
   - **Net guidance for this task** — 1–3 sentences tying the above to the plan.

   If nothing relevant matched, say so plainly in one line.

## Guardrails

- **Read-only.** Never write, edit, archive, or capture. (`Read, Glob, Grep` only.)
- **Index-first, bodies on demand, ≤~7 bodies** — never load a store wholesale.
- **Return synthesis, not raw files** — the planner's budget is the whole point.
- **Cite ids + scope** for every lesson, and surface **corrections first**.
- Honour the two tiers; **project shadows global** on id collision.
