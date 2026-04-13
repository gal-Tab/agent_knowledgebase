---
description: Compile new or updated source files from raw/ into structured wiki pages. Dispatches background agents for extraction and compilation.
allowed-tools: Bash(python3:*), Bash(shasum:*), Bash(cp:*), Bash(command:*), Bash(mkdir:*), Bash(rm:*), Bash(git add:*), Bash(git commit:*), Bash(git status:*), Read, Write, Edit, Glob, Grep, Agent
---

# Compile Knowledge Base Sources

Process all uncompiled or updated files in `raw/` through the extraction and compilation pipeline. Dispatches background agents for parallel source extraction, then resolves entities/concepts sequentially.

---

## Step 1: Read State

Read three files and hold their contents — they're needed throughout compilation:

1. `wiki-schema.md` — domain rules (embedded in worker prompts)
2. `raw/.manifest.json` — pipeline state
3. `wiki/index.md` — existing wiki pages

---

## Step 2: Identify Files to Process

From the manifest, identify files that need work:

| Condition | Action |
|-----------|--------|
| File in `raw/` but not in manifest | New file — extract and compile |
| `status: "extracted"` with `compiled_at: null` | Interrupted compilation — resume from source page creation |
| `status: "compiled"` but sha256 differs from current file | Updated file — re-extract and re-compile |
| `status: "failed"` | Previously failed — retry |

If no files need processing, tell the user `"All files are up to date."` and stop.

**Repo ingestion:** Repos are NOT dropped into `raw/` as files. When the user asks to ingest a repo, use `tools/extract-repo.sh <url-or-path> raw/.extracted/{name}.extracted.md` directly. Track by URL or path as the manifest key instead of a filename.

Tell the user: `"Found N file(s) to compile: file1.md, file2.pdf"`

---

## Step 3: Dependency Pre-Check

Before any extraction, verify required tools per file format:

| Extension | Check command | Skip message |
|-----------|--------------|-------------|
| `.pdf` | `python3 -c "import pymupdf4llm"` | `"Skipping {file}: pymupdf4llm not installed. Run: pip3 install --user pymupdf4llm"` |
| repo | `command -v repomix` or `command -v npx` | `"Skipping {file}: repomix not found. Run: npm install -g repomix"` |
| `.md`, `.txt` | (none) | N/A |

Remove failing files from the work list. If all files fail dep checks, report and stop.

Tell the user: `"Dependencies OK. Starting compilation..."`

---

## Step 4: Dispatch Workers

Create the results directory:

```bash
mkdir -p raw/.compile-results
```

For each file, check its size to inform the worker's reading strategy:

```bash
python3 -c "import os; s=os.path.getsize('raw/{file}'); print('small' if s<80000 else 'medium' if s<250000 else 'large')"
```

For each file, spawn one background agent:

```
Agent(
  subagent_type="general-purpose",
  model="sonnet",
  run_in_background=true,
  prompt="[Worker prompt — see Step 4a below, with all {placeholders} filled]"
)
```

Issue ALL Agent calls in a single message for parallel execution.

Tell the user:
- 1 file: `"Compiling {filename} in background. You can continue working."`
- N files: `"Compiling {N} files in parallel. You can continue working."`

**Fallback — Agent tool unavailable:** If the Agent tool is not available, process files sequentially in the main process. For each file, run the extraction (Step 4a parts 1-3) directly, then continue to Step 6 for entity resolution. This re-introduces source tokens into the main context window — this is the known limitation from before this change.

### Step 4a: Worker Prompt

This is the complete prompt embedded in each Agent call. Fill all `{placeholders}` with actual values before dispatching.

```
You are a knowledge base compilation worker. Your job: extract ONE source file, read it, and create a source summary page. You do NOT create entity or concept pages. You do NOT touch the index, manifest, or git.

## Domain Rules

{Insert the full text of wiki-schema.md here}

## Your Assignment

- Source file: raw/{filename}
- File format: {pdf|md|txt}
- Project directory: {absolute path to project root}
- Extract tool path: {absolute path to tools/extract-pdf.py or tools/extract-repo.sh}
- Estimated source size: {small|medium|large}

## Instructions

### 1. Extract

Run the appropriate extraction command:

For PDF:
  python3 {project}/tools/extract-pdf.py {project}/raw/{filename} {project}/raw/.extracted/{basename}.extracted.md

For markdown/text:
  cp {project}/raw/{filename} {project}/raw/.extracted/{basename}.extracted.md

For repo:
  {project}/tools/extract-repo.sh {url-or-path} {project}/raw/.extracted/{name}.extracted.md

Compute the sha256 hash of the original source file:
  shasum -a 256 {project}/raw/{filename} | cut -d' ' -f1

If extraction fails, write a failure result (see step 4) and stop.

### 2. Read the Extracted Content

Read the extracted markdown from raw/.extracted/{basename}.extracted.md.

**Size-aware reading strategy:**

First, check the file size:
  python3 -c "import os; print(os.path.getsize('{project}/raw/.extracted/{basename}.extracted.md'))"

**Under 80KB (~20K tokens):** Read the full file in one call.

**80KB-250KB (~20K-60K tokens):** Read in chunks using the Read tool's offset/limit parameters. Read 2000 lines per call. Process all chunks — you have context capacity for this.

**Over 250KB (~60K+ tokens):** Selective reading. Do NOT attempt to read the full file.
  1. Read the first 500 lines (introduction, abstract, overview)
  2. Use Grep to find heading patterns and get the document structure:
       Pattern: "^#" in file raw/.extracted/{basename}.extracted.md
  3. Read the key sections: introduction, conclusion/summary, results/findings, methodology (by offset/limit targeting the line numbers from step 2)
  4. Summarize based on selective reading. Note in the source page: "Source summarized via selective reading (document exceeds 60K tokens)."

This ensures quality degrades gracefully rather than failing silently on large documents.

### 3. Create the Source Page

Create wiki/sources/{slug}.md following the source page template from the domain rules above.

Slug derivation:
- Papers/articles: abbreviated title, lowercase, hyphens. "Attention Is All You Need" → attention-is-all-you-need
- Books: author-lastname-short-title. "Deep Learning by Goodfellow" → goodfellow-deep-learning
- Repos: repo name. github.com/user/my-tool → my-tool
- General docs: descriptive short name. company-overview.md → company-overview

Source page structure: follow the sections in the domain rules (Overview, Key Claims, Evidence/Data, Limitations, Cross-References). Keep under 1500 words — summarize aggressively for longer sources.

At the bottom of the source page, add this temporary section:

## Extracted References
- Entity: {Name} — {one-line description} (type: {person|org|product|place|tool|project})
- Concept: {Name} — {one-line description}

Entity extraction rules:
- Only entities central to the source's thesis, not merely cited
- Multi-author papers: at most 3 authors (first author + most notable co-authors)
- Organizations: only if they produced or funded the work

Concept extraction rules:
- Only domain-specific, novel, or defined-by-source concepts
- Skip widely-known general concepts unless the source offers novel treatment
- If the domain description above is blank/general, only extract concepts coined or defined by the source

### 3b. Create Full-Source Preservation (Candlekeep Hybrid)

After creating the source summary page, preserve the original document structure for deep citation:

1. Create directory: `wiki/full-sources/{slug}/`

2. Generate `wiki/full-sources/{slug}/toc.md` — a table of contents built from the extracted document's headings:
   ```markdown
   # {Source Title} — Table of Contents
   
   - [Page 1](page-1.md) — {first heading or "Introduction"}
   - [Page 2](page-2.md) — {heading at start of page 2}
   ...
   ```

3. Split the extracted content into `wiki/full-sources/{slug}/page-{N}.md` files, each ~2000 words (split at heading boundaries when possible). Each page preserves the original text verbatim — no summarization.

4. Add to the source summary page frontmatter: `full_source: "full-sources/{slug}/"`

This is additive — the wiki summary still works as before, but agents can "drill down" to original text when the summary isn't sufficient.

**Skip this step if the extracted content is under 500 words** (no benefit to pagination for short documents).

### 4. Write Result File

Write a JSON file to raw/.compile-results/{slug}.json with this exact structure:

{
  "source_file": "{filename}",
  "slug": "{slug}",
  "source_page": "wiki/sources/{slug}.md",
  "status": "success",
  "error": null,
  "sha256": "{hash from step 1}",
  "extracted_at": "{ISO 8601 timestamp}"
}

If extraction or compilation failed, write:
{
  "source_file": "{filename}",
  "slug": "{slug or basename}",
  "source_page": null,
  "status": "failed",
  "error": "{what went wrong}",
  "sha256": null,
  "extracted_at": null
}

You are done. Do not update wiki/index.md, raw/.manifest.json, or make any git commits.
```

---

## Step 5: Collect Results

After all agents complete, read each result file from `raw/.compile-results/`:

```
Glob: raw/.compile-results/*.json
```

For each result file, read the JSON. Expected structure:

```json
{
  "source_file": "paper.pdf",
  "slug": "attention-is-all-you-need",
  "source_page": "wiki/sources/attention-is-all-you-need.md",
  "status": "success",
  "error": null,
  "sha256": "abc123...",
  "extracted_at": "2026-04-06T12:00:00Z"
}
```

**If a result file is missing:** Glob for `wiki/sources/*.md` files that weren't there before dispatch. If a source page exists without a result JSON, treat as success with unknown metadata and log a warning.

**If `status: "failed"`:** Log the failure. Set the file's manifest entry to `"failed"` with the error message. Continue with successful files.

Tell the user per file:
- Success: `"Extracted: {filename} → {source_page}"`
- Failure: `"Failed: {filename} — {error}"`

**If ALL files failed:** Update the manifest with failure statuses (Step 8b), report failures (Step 10), and stop. Do not attempt entity resolution, link validation, or git commit — there are no wiki pages to process.

---

## Step 6: Entity/Concept Resolution

For each successfully compiled source page, process entities and concepts **sequentially** (one source at a time, in the main process). This ensures entity/concept pages reflect real-time wiki state — no race conditions.

### 6a: Read and Parse

1. Read `wiki/sources/{slug}.md` (~1500 words — the summarized source page, NOT the original 32K source file)
2. Find the `## Extracted References` section
3. Parse each line for entity and concept candidates

### 6b: Check for Existing Pages

For each candidate:

1. Read `wiki/index.md` (re-read each iteration to see updates from prior candidates)
2. Normalize the candidate name: lowercase, strip Inc/Ltd/Corp/LLC, compare against existing slugs and aliases
3. If a page already exists → read it. Update ONLY if the new source adds meaningful new information (new facts, new context, or contradictions). Append to relevant sections — never rewrite existing content.
4. If no page exists → apply creation thresholds before creating

### 6c: Creation Thresholds

- **Entity:** Create if central to any source's thesis OR mentioned in 2+ existing sources. Do NOT create thin pages for minor mentions.
- **Concept:** Create only if domain-specific or novel. When in doubt, don't create — the concept can be promoted later when more sources reference it.
- **Comparison:** Only create if explicitly requested by the user OR two sources clearly contradict each other on the same topic.

### 6d: Entity Page Structure

Follow wiki-schema.md. Typically:

```yaml
---
title: "{Entity Name}"
type: entity
source_refs:
  - slug: "{source-slug}"
    confidence: STATED|INFERRED|UNCERTAIN
created: {YYYY-MM-DD}
updated: {YYYY-MM-DD}
tags: []
---
```

Sections: Overview, Key Facts, Source Appearances. End with `## See Also` listing related pages.

**Confidence on cross-references:** Assign a confidence label to every cross-reference:
- `STATED` — the relationship is explicitly stated in the source text
- `INFERRED` — the relationship is a logical deduction from context (e.g., co-authorship implies collaboration)
- `UNCERTAIN` — the relationship is ambiguous or weakly supported

Format See Also links with confidence tags: `[Entity Name](../entities/name.md) [STATED]`

### 6e: Concept Page Structure

```yaml
---
title: "{Concept Name}"
type: concept
aliases: []
domain_tags: []
source_refs:
  - slug: "{source-slug}"
    confidence: STATED|INFERRED|UNCERTAIN
created: {YYYY-MM-DD}
updated: {YYYY-MM-DD}
tags: []
---
```

Sections: Definition, Context, Related Concepts. End with `## See Also` with confidence labels on each link.

### 6f: Contradiction Handling

If a new source contradicts information in an existing page, flag it inline:

```markdown
**[Contradiction]** Source A claims X, but Source B claims Y.
```

Do NOT silently overwrite the previous claim.

### 6g: Clean Up Source Page

After resolving all candidates, remove the `## Extracted References` section from the source page. The candidates are now resolved into actual pages.

Tell the user per source: `"Resolved: {source-title} → +{N} entities, +{M} concepts"`

Track all pages created and updated across all sources for use in Steps 7-9.

---

## Step 7: Link Validation

For each page created or updated in this compile run (source pages from Step 5 + entity/concept pages from Step 6):

1. Read the page content
2. Find all markdown links matching the pattern `](...*.md)`
3. For each link, resolve the relative path from the page's directory and check if the target file exists using Glob
4. Collect broken links

Report as warnings — do NOT block the commit:

```
"Link warning: wiki/sources/scaling-laws.md → ../entities/kaplan-jared.md (not found)"
"N links validated, M broken."
```

If zero broken links: `"All cross-references valid."`

---

## Step 8: Update Index + Manifest

### 8a: Update wiki/index.md

Add entries for all new and updated pages. Format:

```markdown
- [{Title}](sources/{slug}.md) — {one-line description}
```

Update the page counts in section headers. Update the "Updated:" date.

### 8b: Update raw/.manifest.json

For each compiled file:
- Set `status` to `"compiled"`
- Set `source_page` to the wiki path
- Set `wiki_pages` to array of all pages created/updated for this source
- Set `compiled_at` to current ISO timestamp
- Set `sha256` to the hash from the result file

For failed files:
- Set `status` to `"failed"`
- Set `error` to the failure reason

### 8c: Clean Up

Remove temporary compile results:

```bash
rm -rf raw/.compile-results/
```

### 8d: Index Tier Transition

If total wiki pages exceed 100, split index into category sub-indexes:
- `wiki/index.md` becomes a meta-index (category names + counts + links)
- Create `wiki/sources/_index.md`, `wiki/entities/_index.md`, `wiki/concepts/_index.md`, `wiki/comparisons/_index.md`

### 8e: Generate Relationship Graph

Generate a Mermaid diagram showing entity↔source↔concept relationships:

```bash
python3 tools/generate-graph.py wiki wiki/graph.mmd
```

This reads page frontmatter (key_entities, key_concepts, source_refs) and produces a visual relationship map. The graph is regenerated on every compile run.

If `tools/generate-graph.py` is not available (e.g., not copied during kb-init), skip this step silently.

---

## Step 9: Git Commit

Stage all changed files in `wiki/`, `raw/.manifest.json`. Single commit:

- Single file: `[compile] {source-title} | +{new} ~{updated} pages`
- Batch: `[compile] Batch: file1, file2 | +{new} ~{updated} pages`

---

## Step 10: Summary

Report compilation results to the user:

```
Compilation complete.
  Sources compiled: N
  Pages created: X (Y sources, Z entities, W concepts)
  Pages updated: M
  Failures: F (with reasons)
  Broken links: L (with details)
  Wiki total: T pages (Xs/Ye/Zc/Wn)
```
