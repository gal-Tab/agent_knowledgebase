# LLM Wiki Agent — Design Specification

## Context

We need a Claude Code project agent that maintains a personal knowledge base as a compiled markdown wiki. The agent auto-ingests source files (PDF, markdown, git repos), compiles them into structured wiki pages, and consults the wiki when answering domain questions — all without explicit commands.

**Problem:** Claude Code sessions start fresh each time. Domain knowledge must be re-explained or re-discovered. Files uploaded to conversations are lost between sessions. There's no persistent, structured knowledge layer.

**Solution:** A template repo you clone into any project. It provides CLAUDE.md instructions, hooks, and extraction tools that turn Claude into a knowledge-base-maintaining agent. The wiki compounds over time — every source ingested makes future sessions smarter.

**Inspired by:** Karpathy's "LLM Knowledge Bases" pattern, Cole Medin's git-as-memory, CandleKeep's auto-detection model.

---

## Design Principles

1. **Project agent pattern.** A template repo cloned per project. Each project gets its own domain-specific wiki.
2. **Hook-driven, not command-driven.** No `/wiki-ingest` or `/wiki-query`. Agent detects new files and recognizes domain questions autonomously.
3. **Two human actions only.** Drop a file into `raw/`. Ask a question. Everything else is automatic.
4. **Three sources of truth, three concerns.** Manifest = pipeline state. HANDOFF.md = session state. Git = change history. No redundancy.
5. **Convention over configuration.** CLAUDE.md sections, not scattered config files. One hook script, not three.
6. **wiki-schema.md is the pluggable part.** The engine (CLAUDE.md + hooks + tools) is generic. The domain rules are in wiki-schema.md. Same template, different schemas.

---

## Architecture

### Three Layers

```
L2: BEHAVIOR  — wiki-schema.md (domain-specific compilation rules, pluggable per project)
L1: KNOWLEDGE — raw/ → extract → compile → wiki/ (the compiled wiki)
L0: INFRA     — hooks + extraction tools + git
```

### File Structure

```
project-root/
├── .claude/
│   ├── settings.json              # Hook config: SessionStart + UserPromptSubmit → kb-hook.sh
│   └── hooks/
│       └── kb-hook.sh             # ONE script: scan raw/, git log, wiki stats → additionalContext
│
├── raw/                           # HUMAN drops files here
│   ├── .manifest.json             # Pipeline state: file → extraction/compilation status + sha256
│   ├── .extracted/                # Auto-generated clean markdown (never edit)
│   │   ├── paper.extracted.md
│   │   └── my-repo.extracted.md
│   └── {paper.pdf, notes.md, https___github.com_user_repo, ...}
│
├── wiki/                          # AGENT writes & maintains (human never edits directly)
│   ├── index.md                   # Content catalog (flat → tiered at 100+ pages)
│   ├── sources/                   # One summary per raw source
│   │   └── {source-slug}.md
│   ├── entities/                  # People, orgs, products, places
│   │   └── {entity-slug}.md
│   ├── concepts/                  # Ideas, frameworks, patterns, definitions
│   │   └── {concept-slug}.md
│   └── comparisons/               # Cross-source analysis (created on demand)
│       └── {topic-slug}.md
│
├── tools/                         # Format extraction wrappers
│   ├── extract-pdf.py             # pymupdf4llm wrapper
│   └── extract-repo.sh            # repomix wrapper
│
├── wiki-schema.md                 # Domain-specific compilation rules (THE pluggable part)
├── HANDOFF.md                     # Session state (auto-managed by agent)
├── CLAUDE.md                      # Core agent instructions (same across all projects)
└── setup.sh                       # Install dependencies
```

**~12 files** for the template. Wiki pages grow organically from there.

---

## Subsystem 1: Ingestion Pipeline

### File Detection

Two hooks call the same script:

**`.claude/settings.json`:**
```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/kb-hook.sh"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/kb-hook.sh"
          }
        ]
      }
    ]
  }
}
```

**`kb-hook.sh`** does three things:
1. Compares `raw/` files against `raw/.manifest.json` → lists unprocessed/updated files
2. Reads `git log --oneline -20` → extracts last `[session]` commit for orientation
3. Counts files in `wiki/` subdirectories → reports stats
4. Returns all as compact stdout (becomes `additionalContext`)

Output example:
```
=== KB Status ===
New files in raw/: paper.pdf, notes.md
Updated files: old-paper.pdf (content changed)
Last session: [session] End: compiled 2 sources, 1 query | wiki: 35pp
Wiki stats: 15 sources, 12 entities, 6 concepts, 2 comparisons
```

### Extraction

The agent reads CLAUDE.md extraction instructions and calls the right tool:

| Format | Command | Tool |
|--------|---------|------|
| PDF | `python3 tools/extract-pdf.py raw/file.pdf > raw/.extracted/file.extracted.md` | pymupdf4llm |
| Markdown/Text | `cp raw/file.md raw/.extracted/file.extracted.md` | passthrough |
| Git repo | `tools/extract-repo.sh <repo-path-or-url> > raw/.extracted/repo.extracted.md` | repomix |

**Repo ingestion UX:** User tells the agent "ingest this repo" and provides a URL or local path. The agent calls `extract-repo.sh` directly — repos are NOT dropped into `raw/` as files. The manifest tracks them by URL or path instead of filename.

No router script needed for 3 formats. CLAUDE.md has a simple decision table.

**Extensibility:** Adding a new format = adding a tool script + one line to the CLAUDE.md extraction table. Future additions: EPUB (pandoc), HTML (trafilatura), CSV (pandas), YouTube (yt-dlp), DOCX (pandoc).

### Manifest (`raw/.manifest.json`)

Tracks pipeline state — which files have been extracted, compiled, and what wiki pages they produced:

```json
{
  "paper.pdf": {
    "status": "compiled",
    "extracted": "raw/.extracted/paper.extracted.md",
    "source_page": "wiki/sources/scaling-laws.md",
    "wiki_pages": ["wiki/sources/scaling-laws.md", "wiki/entities/openai.md", "wiki/concepts/scaling-laws.md"],
    "sha256": "a1b2c3d4...",
    "extracted_at": "2026-04-05T14:30:00Z",
    "compiled_at": "2026-04-05T14:35:00Z"
  },
  "notes.md": {
    "status": "extracted",
    "extracted": "raw/.extracted/notes.extracted.md",
    "source_page": null,
    "wiki_pages": [],
    "sha256": "e5f6g7h8...",
    "extracted_at": "2026-04-05T15:00:00Z",
    "compiled_at": null
  }
}
```

**Status values:** `new` → `extracted` → `compiled` | `failed`

The agent updates the manifest after each pipeline step. The hook script reads it to determine what's unprocessed.

**Re-extraction:** If `sha256` of the raw file differs from the manifest entry, the file has been updated. The hook reports it as "Updated files" and the agent re-extracts and re-compiles.

---

## Subsystem 2: Compilation

### Two-Phase Approach

**Phase 1 — Source compilation (immediate):**
1. Agent reads `wiki-schema.md` for domain rules
2. Agent reads `wiki/index.md` to know existing pages
3. Agent reads `raw/.extracted/{file}.extracted.md`
4. Creates `wiki/sources/{slug}.md` with structured summary
5. At the bottom of source page, writes `## Extracted References` — a candidate list of entities and concepts (names + one-line descriptions)

**Phase 2 — Entity/concept resolution (deliberate):**
1. For each candidate in the extracted references:
   - Check `wiki/index.md` for existing page (normalized name matching: lowercase, strip Inc/Ltd/etc.)
   - If page exists → read it, update only if new source adds meaningful new info
   - If new → create page, applying wiki-schema.md thresholds
2. Remove the `## Extracted References` section from the source page (candidates are now resolved)
3. Update `wiki/index.md` with all new/updated pages
4. Update `raw/.manifest.json` with compilation result
5. Git commit: `[compile] {source-title} | +{new} ~{updated} pages`

### wiki-schema.md Format

```markdown
# Wiki Schema

## Domain Description
{2-3 sentences describing what this knowledge base covers.
Leave generic for multi-domain use. Specialize per project.}

## Page Types

### source
Frontmatter: title, source_file, source_type, date_ingested, key_entities[], key_concepts[]
Sections: Overview, Key Claims, Evidence/Data, Limitations, Cross-References
Max length: 1500 words

### entity
Frontmatter: title, type (person|org|product|place|tool), aliases[], source_refs[]
Sections: Overview, Key Facts, Source Appearances
Merge threshold: Create if central to any source OR mentioned in 2+ sources

### concept
Frontmatter: title, aliases[], domain_tags[], source_refs[]
Sections: Definition, Context, Related Concepts
Create threshold: Only if domain-specific or novel (skip common knowledge)

### comparison
Frontmatter: title, compared_entities[], source_refs[]
Sections: Overview, Dimensions, Summary Table, Synthesis
Create threshold: Only when explicitly requested or 2+ sources offer conflicting views

## Frontmatter Template
---
title: ""
type: source|entity|concept|comparison
source_refs: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: []
---

## Link Format
Standard markdown: [Display Text](../category/slug.md)
Backlink section at bottom of every page: ## See Also

## Compilation Rules
- One source summary per raw file, always
- Entity pages: create if central to source OR mentioned in 2+ existing sources
- Concept pages: only for domain-specific or novel concepts
- Comparison pages: only on explicit request or when sources conflict
- When updating an existing page with new source info, append to relevant sections — don't rewrite
- Flag contradictions inline: **[Contradiction]** Source A claims X, Source B claims Y
```

### Page Frontmatter Example

```markdown
---
title: "Scaling Laws for Neural Language Models"
type: source
source_file: raw/scaling-laws-paper.pdf
source_type: pdf
date_ingested: 2026-04-05
key_entities: [openai, kaplan-jared]
key_concepts: [scaling-laws, power-law, compute-optimal-training]
tags: [ml, training, scaling]
created: 2026-04-05
updated: 2026-04-05
---

# Scaling Laws for Neural Language Models

## Overview
...

## Key Claims
...

## Evidence/Data
...

## Limitations
...

## Cross-References
- [OpenAI](../entities/openai.md) — research lab that published this work
- [Scaling Laws](../concepts/scaling-laws.md) — the core concept

## See Also
- [Chinchilla Paper](scaling-chinchilla.md) — follow-up work with different conclusions
```

---

## Subsystem 3: Index & Scale

### Tier 1: Flat Index (0–100 pages)

```markdown
# Wiki Index
Updated: 2026-04-05 | Total: 47 pages

## Sources (23)
- [Scaling Laws Paper](sources/scaling-laws.md) — power-law relationships in LLM training
- [GPT-4 Technical Report](sources/gpt4-report.md) — architecture and evaluation details
...

## Entities (15)
- [OpenAI](entities/openai.md) — AI research lab, creator of GPT series
- [Jared Kaplan](entities/kaplan-jared.md) — scaling laws researcher at OpenAI
...

## Concepts (9)
- [Scaling Laws](concepts/scaling-laws.md) — power-law relationships between compute, data, parameters, and performance
...

## Comparisons (0)
(none yet)
```

Agent reads the full index when compiling or querying. At <100 pages this is ~4KB, well within context budget.

### Tier 2: Category Sub-Indexes (100–300 pages)

When compilation pushes total pages past 100, the agent restructures:
- `wiki/index.md` becomes a meta-index (just category names + counts + link to sub-index)
- `wiki/sources/_index.md`, `wiki/entities/_index.md`, etc. hold the per-category listings
- Agent reads only the relevant sub-index per task

Migration is a one-time operation, triggered automatically by the compilation step.

### Tier 3: Search-Assisted (300+ pages)

Add `grep -rl "search term" wiki/` as the primary discovery mechanism. CLAUDE.md instructs the agent to search before reading indexes at this scale. Can later bolt on `qmd` for BM25+vector hybrid search without architectural changes.

---

## Subsystem 4: Context Management

### Startup Context Budget

| Source | Lines | When |
|--------|-------|------|
| CLAUDE.md | ~80 | Always (core instructions) |
| wiki-schema.md (@import) | ~50 | Always (domain rules) |
| kb-hook.sh additionalContext | ~10 | Always (status, new files, last session) |
| **Total startup** | **~140** | |

### On-Demand Loading

| Resource | When loaded | How |
|----------|------------|-----|
| `wiki/index.md` | Compiling or answering domain question | Agent reads via Read tool |
| Individual wiki pages (2–5) | Answering a specific question | Agent reads relevant pages only |
| `raw/.manifest.json` | Checking pipeline state | Agent reads via Read tool |
| `raw/.extracted/*.md` | During compilation | Agent reads the specific file |

### Query Context Pattern

For domain questions, the agent:
1. Reads `wiki/index.md` to find relevant pages (~4KB)
2. Reads 2–5 relevant wiki pages (~2–8KB each)
3. Synthesizes answer
4. Total query context: ~20–50KB — well within budget

The key constraint from CLAUDE.md: **"Never load the entire wiki. Read index, identify relevant pages, read only those."**

---

## Subsystem 5: Session Persistence

### HANDOFF.md

Written by the agent before session end (instructed by CLAUDE.md):

```markdown
# Handoff
Date: 2026-04-05 14:30 UTC

## Session Summary
Compiled 3 sources, answered 2 queries, created 1 comparison page.

## Wiki Stats
Sources: 23 | Entities: 15 | Concepts: 9 | Comparisons: 3 | Total: 50

## Pending
- raw/paper-z.pdf: extraction failed (scanned PDF, needs OCR mode)
- Entity "Anthropic" mentioned in 3 sources but no dedicated page yet

## Active Research Threads
- User investigating transformer architecture variants
- Comparison between GPT-4 and Claude 3 requested but not yet compiled
```

### Git Commit Convention

```
[compile] Added "Paper Title" | +3 ~2 pages
[compile] Re-compiled "Paper Title" (source updated) | ~4 pages
[query-file] Filed comparison: topic-slug.md
[session] End: compiled 2 sources, answered 1 query | wiki: 50pp
[schema] Updated wiki-schema.md: added comparison thresholds
```

### Cold-Start Sequence

1. `kb-hook.sh` runs → injects: new files, last session commit, wiki stats
2. CLAUDE.md loads with `@wiki-schema.md` import
3. Agent reads HANDOFF.md if referenced by hook output
4. Agent knows: what happened last session, what's pending, what's new

If HANDOFF.md is missing/stale, git log provides fallback orientation.

---

## Subsystem 6: Query & File-Back

### Domain Question Detection

CLAUDE.md-driven heuristics (no LLM classifier):
- User asks about topics that match wiki entity/concept names
- User asks for comparisons between things in the wiki
- User references "my research," "what I've read," "according to..."
- User asks questions in the domain described by wiki-schema.md

When detected, the agent reads index → identifies relevant pages → reads them → synthesizes answer.

### When NOT to Consult Wiki

- Pure coding questions unrelated to domain
- General knowledge questions
- Meta questions about the wiki itself ("how many pages do I have?")
- Questions the agent can answer without domain context

### File-Back (Compounding Loop)

After producing a valuable answer that synthesizes new insights:
1. Agent suggests: "This answer contains cross-references not yet in the wiki. File it back?"
2. If user agrees → agent creates appropriate wiki page (comparison, concept, or enriches existing entity)
3. Updates index.md → updates manifest → git commit: `[query-file] Filed: {title}`

This is the compounding mechanism — every exploration can enrich the knowledge base.

---

## Subsystem 7: Extraction Tools

### extract-pdf.py

```python
#!/usr/bin/env python3
"""Extract PDF to clean markdown using pymupdf4llm."""
import sys
import pymupdf4llm

def main():
    if len(sys.argv) != 2:
        print("Usage: extract-pdf.py <input.pdf>", file=sys.stderr)
        sys.exit(1)
    md = pymupdf4llm.to_markdown(sys.argv[1])
    print(md)

if __name__ == "__main__":
    main()
```

### extract-repo.sh

```bash
#!/bin/bash
# Extract git repo to markdown using repomix
# Usage: extract-repo.sh <repo-path-or-url>
set -euo pipefail

INPUT="$1"

if [[ "$INPUT" == http* ]]; then
    # Remote repo — repomix handles cloning
    repomix --remote "$INPUT" --style markdown
else
    # Local repo
    repomix "$INPUT" --style markdown
fi
```

### setup.sh

```bash
#!/bin/bash
# Install knowledge base dependencies
set -euo pipefail

echo "Installing Python dependencies..."
pip install pymupdf4llm

echo "Installing repomix..."
npm install -g repomix

echo "Creating directory structure..."
mkdir -p raw/.extracted wiki/sources wiki/entities wiki/concepts wiki/comparisons tools

echo "Done. Drop files into raw/ and start a Claude Code session."
```

---

## CLAUDE.md Structure (Outline)

The full CLAUDE.md will have these sections:

```
# Knowledge Base Agent

## Overview
{What this agent does — 3 sentences}

@wiki-schema.md

## Ingestion
{When kb-hook reports new files, extract and compile them FIRST}
{Format → command table: PDF, Markdown, Repo}
{After extraction: run two-phase compilation}
{Update manifest after each step}
{Git commit with [compile] prefix}

## Compilation
{Phase 1: source summary + extracted references}
{Phase 2: entity/concept resolution against index}
{How to check for existing pages, normalize names, handle updates vs. creates}
{Frontmatter requirements}
{Cross-reference and backlink format}

## Querying
{When to consult wiki vs. answer from general knowledge}
{Pattern: read index → identify pages → read 2-5 pages → synthesize}
{Never load entire wiki}
{File-back suggestion when answer produces new insights}

## Lifecycle
{On session start: read kb-hook output, read HANDOFF.md}
{Before session end: update HANDOFF.md, git commit [session]}
{Git commit message convention}
{Index tier transitions: flat → split at 100 pages}

## What NOT to Do
{Never edit wiki pages without reading index first}
{Never load entire wiki into context}
{Never create comparison pages unless explicitly asked or sources conflict}
{Never skip manifest updates}
```

---

## Verification Plan

### Test 1: Single File Ingestion
1. Run `setup.sh`
2. Drop a PDF into `raw/`
3. Start Claude Code session
4. Verify: hook detects file → agent extracts → compiles → creates source page + entity/concept pages → updates index → updates manifest → git commits

### Test 2: Mid-Session File Drop
1. During an active session, drop a markdown file into `raw/`
2. Send any message to the agent
3. Verify: UserPromptSubmit hook detects new file → agent extracts and compiles before responding

### Test 3: Domain Query
1. With a populated wiki (2+ sources), ask a domain question
2. Verify: agent reads index → reads relevant pages → synthesizes answer from wiki content

### Test 4: File-Back
1. Ask a question that produces cross-referencing insights
2. Accept the file-back suggestion
3. Verify: new wiki page created → index updated → git committed

### Test 5: Session Persistence
1. End a session (verify HANDOFF.md written + git commit)
2. Start new session
3. Verify: hook provides orientation → agent knows last session's state → detects any new files

### Test 6: Re-Extraction
1. Modify a file already in `raw/` (change content)
2. Start new session or send a message
3. Verify: hook detects sha256 mismatch → agent re-extracts and re-compiles

### Test 7: Scale Transition
1. Add sources until wiki exceeds 100 pages
2. Verify: agent automatically restructures index into category sub-indexes

### Test 8: Template Portability
1. Clone the template into a fresh project
2. Customize only wiki-schema.md for a different domain
3. Verify: full pipeline works with domain-specific compilation rules

---

## What This Is NOT

- **Not MCP.** No server, no tools API. The agent uses Claude Code's native Read/Grep/Glob.
- **Not RAG.** No embeddings, no vector DB. The wiki IS the retrieval — structured, compiled, maintained.
- **Not a plugin.** No framework, no marketplace. Clone the template, done.
- **Not a note-taking app.** You never write wiki pages. The agent writes everything. You curate sources and ask questions.

---

## Open Questions (Resolved)

| Question | Decision |
|----------|----------|
| Packaging model | Project agent (template repo cloned per project) |
| Day-one formats | PDF + Markdown + Git repos |
| State tracking | Manifest (pipeline) + HANDOFF.md (session) + git (history) |
| Domain specificity | Generic engine + pluggable wiki-schema.md |
| Mid-session detection | UserPromptSubmit hook calling same kb-hook.sh |
| Index strategy | Flat → tiered at 100+ → grep at 300+ |
| Context management | ~140 lines startup, on-demand page loading |
