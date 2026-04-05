# LLM Wiki Agent — Standalone Research & Build Plan

## What This Is

A standalone Claude Code agent that maintains a personal knowledge base as a compiled markdown wiki. No framework dependencies. No plugins required. Two human actions: drop a file, ask a question. Everything else is hooks.

Inspired by Andrej Karpathy's "LLM Knowledge Bases" pattern (April 2026), with session persistence from Cole Medin's git-as-memory approach, and auto-detection from CandleKeep's model.

---

## Design Principles

1. **Standalone agent.** No ECC (everything Claude code repo), no plugins, no framework. Just CLAUDE.md + hooks + a few CLI tools. Portable, forkable, understandable.
2. **Hook-driven, not command-driven.** No `/wiki-ingest` or `/wiki-query`. Agent detects new files in `raw/` automatically. Agent recognizes domain questions and consults wiki autonomously.
3. **Two human actions only.** Drop a file into `raw/` (or tell agent to fetch a URL). Ask a question. Everything else — extraction, compilation, indexing, cross-referencing, linting, git commits — is automatic.
4. **Format-aware ingest.** PDF, EPUB, HTML, CSV, XLSX, YouTube transcripts, images, markdown. Extraction happens before LLM compilation — clean markdown in, structured wiki out.
5. **The wiki is compiled, not indexed.** Knowledge is synthesized once and maintained, not re-derived on every query.
6. **Outputs compound.** Query results filed back into the wiki make it richer over time.
7. **Git log IS the memory.** No separate log file. Structured commits are the audit trail and session orientation.
8. **Domain schemas are the value.** The engine is generic. The domain-specific compile rules in wiki-schema.md are where the real value lives.

---

## Architecture

### File Structure

```
project-root/
├── raw/                            # HUMAN puts files here (any format)
│   ├── article.md                  # Web clipper output
│   ├── book.pdf                    # PDFs
│   ├── report.epub                 # EPUBs  
│   ├── data.csv                    # Spreadsheets
│   ├── video-transcript.txt        # YouTube/podcast transcripts
│   └── .extracted/                 # Auto-generated clean markdown
│       ├── book.extracted.md
│       └── report.extracted.md
│
├── wiki/                           # AGENT writes & maintains (human never edits)
│   ├── index.md                    # Content catalog — agent reads first
│   ├── overview.md                 # High-level synthesis of everything
│   ├── sources/                    # One summary per raw source
│   │   └── {source-slug}.md
│   ├── entities/                   # People, orgs, products, places
│   │   └── {entity-slug}.md
│   ├── concepts/                   # Ideas, frameworks, patterns, definitions
│   │   └── {concept-slug}.md
│   └── comparisons/                # Cross-source analysis
│       └── {topic-slug}.md
│
├── output/                         # Query results, reports, slides
│                                   # Valuable outputs get filed back to wiki/
│
├── tools/                          # Format extraction scripts
│   ├── extract-pdf.sh              # pymupdf4llm or marker wrapper
│   ├── extract-epub.sh             # pandoc wrapper
│   ├── extract-html.sh             # trafilatura wrapper  
│   ├── extract-csv.sh              # pandas-to-markdown wrapper
│   ├── extract-youtube.sh          # yt-dlp transcript extraction
│   └── extract-router.sh           # Detects format → calls right extractor
│
├── wiki-schema.md                  # Domain-specific compilation rules
├── HANDOFF.md                      # Session continuity (auto-managed)
├── CLAUDE.md                       # This file — agent instructions
├── hooks.json                      # Hook definitions
└── .git/                           # Git log = long-term memory
```

### Three Layers

```
┌─────────────────────────────────────────────┐
│  L2: BEHAVIOR                               │
│  wiki-schema.md — domain-specific compile   │
│  rules that evolve as agent learns domain   │
├─────────────────────────────────────────────┤
│  L1: KNOWLEDGE                              │
│  raw/ → extract → compile → wiki/           │
│  index.md + entities + concepts + sources   │
│  query = agent reads wiki autonomously      │
├─────────────────────────────────────────────┤
│  L0: INFRASTRUCTURE                         │
│  Hooks: auto-detect new files, session      │
│  persistence, git commits, lint triggers    │
│  Tools: PDF/EPUB/HTML/CSV extractors        │
└─────────────────────────────────────────────┘
```

### Hooks (Not Commands)

| Trigger | What Happens | Why Not a Command |
|---------|-------------|-------------------|
| Session start | Read HANDOFF.md → wiki-schema.md → index.md → `git log --oneline -10` | Agent needs orientation automatically, not when asked |
| New file detected in `raw/` | Run extract-router.sh → produce .extracted.md → trigger compilation | Human shouldn't have to say "ingest this" — dropping it is the signal |
| Post-compilation | Update index.md → git commit `[compile] {source title}` | Must happen every time, non-negotiable |
| Domain question detected | Agent reads index.md → relevant wiki pages → synthesizes answer | Like CandleKeep: auto-detection, not /query |
| Valuable output produced | Agent asks "File this back to wiki?" → if yes, creates wiki page + updates index | Compound loop — every exploration can add value |
| Session end | Write HANDOFF.md → git commit `[session] {summary}` | Next session needs to pick up cleanly |
| Session start (secondary) | Quick lint scan: count orphans, broken links, stale pages → report silently | Don't wait for human to ask for health check |

### Ingest Pipeline (Format Extraction)

The extraction layer converts any supported format to clean markdown BEFORE the LLM compiles. This is a tooling problem, not an LLM problem.

**Tools to research and select:**

| Format | Primary Tool | Fallback | Notes |
|--------|-------------|----------|-------|
| PDF | `pymupdf4llm` | `marker` by Meta | Best text+table extraction. marker handles complex layouts better but slower |
| EPUB | `pandoc` | `ebooklib` + custom script | pandoc converts chapters to individual .md files |
| HTML | `trafilatura` | `readability-lxml` | Article extraction — strips nav, ads, boilerplate |
| CSV/XLSX | `pandas` → `.to_markdown()` | `csvkit` | Auto-summary: column names, dtypes, sample rows, basic stats |
| YouTube | `yt-dlp --write-auto-sub` | YouTube Transcript API | Extract auto-generated or manual subtitles to .md |
| Images | LLM vision (Claude) | — | Describe image → store description + keep original for reference |
| Markdown | passthrough | — | Already in target format. Copy to .extracted/ as-is |
| DOCX | `pandoc` | `python-docx` | Convert to markdown preserving headings and tables |

**Extraction script pattern:**
```bash
#!/bin/bash
# extract-router.sh
# Detects file format and routes to appropriate extractor
# Produces: raw/.extracted/{filename}.extracted.md

FILE="$1"
EXT="${FILE##*.}"
BASENAME=$(basename "$FILE" ".$EXT")
OUTPUT="raw/.extracted/${BASENAME}.extracted.md"

case "$EXT" in
  pdf)  python3 tools/extract-pdf.py "$FILE" > "$OUTPUT" ;;
  epub) pandoc "$FILE" -t markdown -o "$OUTPUT" ;;
  html) python3 -m trafilatura --input-file "$FILE" > "$OUTPUT" ;;
  csv)  python3 tools/extract-csv.py "$FILE" > "$OUTPUT" ;;
  xlsx) python3 tools/extract-csv.py "$FILE" > "$OUTPUT" ;;
  docx) pandoc "$FILE" -t markdown -o "$OUTPUT" ;;
  md|txt) cp "$FILE" "$OUTPUT" ;;
  *)    echo "Unsupported format: $EXT" >&2; exit 1 ;;
esac
```

---

## Research Phase — DO THIS FIRST

Before building anything, research each topic below. Create `research/` directory with one markdown file per topic. Read actual source code / documentation, don't guess.

### 1. Format Extraction Tooling
**Goal:** Select and test the best extraction tool for each format.

Research tasks:
- Install and test `pymupdf4llm` on a real PDF with tables and images. Compare output quality with `marker`.
- Test `pandoc` EPUB→markdown conversion. Does it preserve chapter structure? How does it handle images?
- Test `trafilatura` on 3 different article URLs. Compare with `readability-lxml`. Which strips boilerplate better?
- Test `pandas` `.to_markdown()` on a CSV with mixed types. What summary metadata should we auto-generate?
- Test `yt-dlp --write-auto-sub` on a YouTube video. What format does the transcript come in? How to clean it?
- Determine: which tools need pip install? Which are available via homebrew? Build a `setup.sh` that installs all dependencies.
- Test edge cases: scanned PDFs (need OCR?), Hebrew text in PDFs, large EPUBs (500+ pages), password-protected PDFs.

**Output:** `research/extraction-tooling.md` with test results, selected tools, and installation commands.

### 2. Compilation Schema Design
**Goal:** Design the wiki-schema.md format and the compilation prompts.

Research tasks:
- Read Karpathy's gist carefully: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f — focus on the "schema" layer description
- Read rvk7895/llm-knowledge-bases SKILL.md files — how does it instruct the agent to compile?
- Design wiki page frontmatter (YAML): what metadata does each page need? (tags, source_refs, created, updated, backlinks_count)
- Design index.md format: how should entries be organized? By category? By recency? Both?
- Design the compilation prompt: given a raw extracted markdown, what instructions produce good wiki pages?
- Design: how does the agent decide whether to create a new entity/concept page vs. update an existing one?
- Design: how are backlinks formatted? Obsidian-style `[[page-name]]` or standard markdown `[text](path)`?
- Design: what does a "contradiction flag" look like in practice?
- Create 2-3 example domain schemas: one for investment research, one for technical learning, one for product strategy.

**Output:** `research/schema-design.md` with full schema spec, example schemas, and compilation prompt drafts.

### 3. Auto-Detection Patterns
**Goal:** Design how the agent automatically detects (a) new files to ingest and (b) domain questions to answer from wiki.

Research tasks:
- Research: how does CandleKeep's agent auto-detect research questions? What trigger patterns does it use?
- Design: file detection — on session start, how does agent find un-processed files in raw/? Compare: check for missing .extracted.md counterpart vs. git status for new untracked files vs. manifest file
- Design: question detection — what makes a question "answerable from wiki" vs. general knowledge? Heuristics: mentions domain entities? Asks for comparison? References sources? Uses phrases like "according to my research"?
- Design: when should the agent NOT consult the wiki? (pure coding questions, general knowledge, meta questions about the wiki itself)
- Research: how to implement file watching in Claude Code hooks. Can a hook scan a directory? Can it run on session start?

**Output:** `research/auto-detection-design.md`

### 4. Session Persistence & Orientation
**Goal:** Design cold-start orientation without any framework dependency.

Research tasks:
- Design HANDOFF.md format: what fields? (last_session_date, actions_taken, pending_lint_issues, active_research_threads, wiki_stats)
- Design the orientation sequence: what does the agent read, in what order, on session start?
  - Proposed: HANDOFF.md → wiki-schema.md → index.md → `git log --oneline -10`
- Design: how much of the wiki does the agent load into context on start? (just index? Index + overview? Depends on question?)
- Design: git commit message format for each operation type:
  - `[compile] Added source: {title} — {n} pages updated`
  - `[lint] Fixed {n} issues: {summary}`  
  - `[query-file] Filed output: {title}`
  - `[session] End: {summary of actions}`
- Research: minimal git hook setup (post-commit isn't needed — agent commits directly)

**Output:** `research/session-persistence-design.md`

### 5. Lint & Health Check Design
**Goal:** Design automated wiki health checks.

Research tasks:
- Design lint checks:
  - Orphan pages (no inbound links from any other page)
  - Broken backlinks (link targets that don't exist)
  - Contradictions (two pages making conflicting claims about the same entity/concept)
  - Stale claims (source was updated but wiki page wasn't)
  - Missing pages (concept mentioned across multiple pages but has no dedicated page)
  - Missing cross-references (two pages discuss related topics but don't link to each other)
  - Thin pages (less than N words — candidate for merging or expanding)
  - Data gaps (topics where web search could fill missing info)
- Design: lint report format. Severity levels (critical / warning / suggestion)?
- Design: should lint auto-fix anything? (Recommendation: only auto-fix broken links and missing index entries. Everything else: report and ask.)
- Design: how often to lint? (On every session start? Only when wiki exceeds N pages? On-demand only?)

**Output:** `research/lint-design.md`

### 6. Scale Strategy
**Goal:** Determine when the simple architecture breaks and what to do about it.

Research tasks:
- Research: at what wiki size does index.md navigation break down? (Karpathy says ~100 articles / 400K words works fine)
- Research `qmd` (https://github.com/tobi/qmd): local markdown search with BM25 + vector hybrid. Install and test.
- Research alternatives: ripgrep + custom ranking script, simple TF-IDF, Obsidian search API
- Design: tiered strategy — index.md for <100 pages, add search tool at 100+, consider splitting wiki at 500+?
- Research: does Obsidian graph view help the agent? Or is it human-only?
- Research: context window management — how much wiki content can fit in one Claude Code session? At what point do we need selective loading?

**Output:** `research/scale-strategy.md`

---

## Build Phase — After Research Is Complete

### Phase 1: Extraction Tools (2 hrs)
1. Install all selected extraction tools (`setup.sh`)
2. Build `extract-router.sh` with format detection
3. Build individual extractor scripts (pdf, epub, html, csv, youtube)
4. Test each extractor on real files — verify clean markdown output
5. Handle edge cases: Hebrew text, scanned PDFs, large files

### Phase 2: Core Agent (2-3 hrs)
1. Write CLAUDE.md with full agent instructions
2. Write hooks.json: session-start (orientation), file-detection (ingest trigger), session-end (handoff)
3. Write wiki-schema.md template with compilation prompts
4. Build the compilation flow: extracted.md → agent reads → creates/updates wiki pages → updates index → git commits
5. Test: drop a file into raw/ → verify full pipeline runs

### Phase 3: Query & File-Back (1-2 hrs)
1. Implement auto-detection for domain questions
2. Build the query flow: read index → identify pages → read pages → synthesize
3. Build the file-back flow: agent asks "file this?" → creates wiki page → updates index
4. Test: ask a question that requires cross-referencing multiple sources

### Phase 4: Lint & Polish (1-2 hrs)
1. Implement lint checks from research findings
2. Wire lint to session-start hook (quick scan, report silently)
3. Test cross-session persistence: close session → reopen → verify agent orients correctly
4. Test the full cycle: ingest → query → file-back → lint → next session orientation

### Phase 5: Second Domain (1 hr)
1. Create a second wiki-schema.md for a different domain
2. Test that the same agent infrastructure works with different schemas
3. Document the pattern for creating new domain wikis

---

## What This Is NOT

- **Not a plugin.** No marketplace, no /plugin install. Clone the repo, done.
- **Not ECC.** No 142 skills, no 36 agents, no framework. Cherry-picks ideas (session hooks, git memory) but builds clean.
- **Not CandleKeep.** No cloud, no paid tier, no vendor. Same auto-detection concept but over local files.
- **Not RAG.** No embeddings, no vector DB, no chunking. The wiki IS the retrieval — structured, compiled, maintained.
- **Not a note-taking app.** You never write wiki pages. The LLM writes everything. You curate sources and ask questions.

---

## References

- Karpathy gist: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- Karpathy X post: https://x.com/karpathy/status/2039805659525644595  
- Cole Medin's git-as-memory pattern
- CandleKeep auto-detection model: https://getcandlekeep.com
- rvk7895 implementation: https://github.com/rvk7895/llm-knowledge-bases
- qmd search: https://github.com/tobi/qmd
- pymupdf4llm: https://pypi.org/project/pymupdf4llm/
- marker (Meta): https://github.com/VikParuchuri/marker
- trafilatura: https://github.com/adbar/trafilatura

---

## Status

- [ ] Research: Extraction tooling
- [ ] Research: Schema design
- [ ] Research: Auto-detection patterns
- [ ] Research: Session persistence
- [ ] Research: Lint design
- [ ] Research: Scale strategy
- [ ] Build Phase 1: Extraction tools
- [ ] Build Phase 2: Core agent
- [ ] Build Phase 3: Query & file-back
- [ ] Build Phase 4: Lint & polish
- [ ] Build Phase 5: Second domain
