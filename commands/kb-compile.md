---
description: Compile new or updated source files from raw/ into structured wiki pages. Extracts content, creates source summaries, and resolves entities and concepts.
allowed-tools: Bash(python3:*), Bash(shasum:*), Bash(cp:*), Bash(chmod:*), Bash(git add:*), Bash(git commit:*), Bash(git status:*), Read, Write, Edit, Glob, Grep
---

# Compile Knowledge Base Sources

Process all uncompiled or updated files in `raw/` through the extraction and compilation pipeline.

---

## Step 0: Read Domain Rules

Read `wiki-schema.md` from the project root. These rules govern page types, creation thresholds, frontmatter templates, and section structure. Everything you produce must conform to these rules.

Read `raw/.manifest.json` to understand current pipeline state.

Read `wiki/index.md` to know what wiki pages already exist.

---

## Step 1: Identify Files to Process

From the manifest, identify files that need work:

| Condition | Action |
|-----------|--------|
| File in `raw/` but not in manifest | New file — extract and compile |
| `status: "extracted"` with `compiled_at: null` | Interrupted compilation — resume from Phase 1 |
| `status: "compiled"` but sha256 differs from current file | Updated file — re-extract and re-compile |
| `status: "failed"` | Previously failed — retry extraction |

If no files need processing, tell the user "All files are up to date" and stop.

**Repo ingestion:** Repos are NOT dropped into `raw/` as files. When the user asks to ingest a repo, use `tools/extract-repo.sh <url-or-path> raw/.extracted/{name}.extracted.md` directly. Track by URL or path as the manifest key instead of a filename.

---

## Step 2: Extraction

For each file that needs extraction, determine format by extension and run the appropriate command:

| Extension | Command | Notes |
|-----------|---------|-------|
| `.pdf` | `python3 tools/extract-pdf.py raw/{file} raw/.extracted/{basename}.extracted.md` | Uses pymupdf4llm |
| `.md`, `.txt` | `cp raw/{file} raw/.extracted/{basename}.extracted.md` | Passthrough |
| repo (URL/path) | `tools/extract-repo.sh {url-or-path} raw/.extracted/{name}.extracted.md` | Uses repomix |

After each successful extraction, update `raw/.manifest.json`:

```json
{
  "filename": {
    "status": "extracted",
    "extracted": "raw/.extracted/{basename}.extracted.md",
    "source_page": null,
    "wiki_pages": [],
    "sha256": "{hash}",
    "extracted_at": "{ISO timestamp}",
    "compiled_at": null
  }
}
```

Compute sha256: `shasum -a 256 raw/{file} | cut -d' ' -f1`

**Error handling:** If extraction fails, set status to `"failed"` with an `"error"` field describing the failure. Continue processing other files. Do not stop the pipeline for one bad file.

---

## Step 3: Phase 1 — Source Page Compilation

For each extracted file, create a source page:

1. Read the extracted markdown from `raw/.extracted/{basename}.extracted.md`
2. Create `wiki/sources/{slug}.md` following the source page template from wiki-schema.md

### Slug Derivation Rules

- **Papers/articles:** Use the abbreviated title, lowercase, hyphens. "Attention Is All You Need" → `attention-is-all-you-need`. "Scaling Laws for Neural Language Models" → `scaling-laws-neural-lm`.
- **Books:** Author-last-name + short-title. "Deep Learning by Goodfellow" → `goodfellow-deep-learning`.
- **Repos:** Repo name. `github.com/user/my-tool` → `my-tool`.
- **General docs:** Descriptive short name. `company-overview.md` → `company-overview`.

### Source Page Structure

Follow the sections defined in wiki-schema.md (typically: Overview, Key Claims, Evidence/Data, Limitations, Cross-References). Keep the source page under 1500 words — summarize aggressively for longer sources.

### Extracted References

At the bottom of the source page, add a temporary section listing candidate entities and concepts:

```markdown
## Extracted References
- Entity: {Name} — {one-line description} (type: {person|org|product|place|tool|project})
- Concept: {Name} — {one-line description}
```

**Entity extraction rules:**
- Extract entities that are central to the source's thesis, not merely cited
- For multi-author papers: list at most 3 authors (first author + most notable co-authors). Other authors appear only in the source page, not as entity candidates.
- Organizations: extract if they produced or funded the work

**Concept extraction rules:**
- Extract concepts that are domain-specific, novel, or defined by the source
- Skip widely-known general concepts unless the source offers a unique perspective
- If the domain description in wiki-schema.md is blank/general, only extract concepts that are coined or defined by the source itself

---

## Step 4: Phase 2 — Entity/Concept Resolution

For each candidate in Extracted References:

### Check for Existing Pages

1. Read `wiki/index.md`
2. Normalize the candidate name: lowercase, strip Inc/Ltd/Corp/LLC, compare against existing slugs and aliases
3. If a page already exists → read it. Update ONLY if the new source adds meaningful new information (new facts, new context, or contradictions). Append to relevant sections — never rewrite existing content.
4. If no page exists → apply creation thresholds from wiki-schema.md before creating

### Creation Thresholds

- **Entity:** Create if central to any source's thesis OR mentioned in 2+ existing sources. Do NOT create thin pages for minor mentions.
- **Concept:** Create only if domain-specific or novel. When in doubt, don't create — the concept can be promoted later when more sources reference it.
- **Comparison:** Only create if explicitly requested by the user OR two sources clearly contradict each other on the same topic.

### Entity Page Structure

Follow wiki-schema.md. Typically:

```yaml
---
title: "{Entity Name}"
type: entity
source_refs: ["{source-slug}"]
created: {YYYY-MM-DD}
updated: {YYYY-MM-DD}
tags: []
---
```

Sections: Overview, Key Facts, Source Appearances. End with `## See Also` listing related pages.

### Concept Page Structure

```yaml
---
title: "{Concept Name}"
type: concept
aliases: []
domain_tags: []
source_refs: ["{source-slug}"]
created: {YYYY-MM-DD}
updated: {YYYY-MM-DD}
tags: []
---
```

Sections: Definition, Context, Related Concepts. End with `## See Also`.

### Contradiction Handling

If a new source contradicts information in an existing page, flag it inline:

```markdown
**[Contradiction]** Source A claims X, but Source B claims Y.
```

Do NOT silently overwrite the previous claim.

---

## Step 5: Finalize

1. **Remove Extracted References** — delete the `## Extracted References` section from the source page (candidates are now resolved)

2. **Update wiki/index.md** — add entries for all new and updated pages. Format:
   ```markdown
   - [{Title}](sources/{slug}.md) — {one-line description}
   ```
   Update the page counts in section headers. Update the "Updated:" date.

3. **Update raw/.manifest.json** — for each compiled file:
   - Set `status` to `"compiled"`
   - Set `source_page` to the source page path
   - Set `wiki_pages` to array of all pages created/updated
   - Set `compiled_at` to current ISO timestamp

4. **Check index tier transition** — if total pages exceed 100, split index into category sub-indexes:
   - `wiki/index.md` becomes a meta-index (category names + counts + links)
   - Create `wiki/sources/_index.md`, `wiki/entities/_index.md`, `wiki/concepts/_index.md`, `wiki/comparisons/_index.md`

5. **Git commit:**
   ```
   [compile] {source-title} | +{new} ~{updated} pages
   ```
   Stage all changed files in `wiki/`, `raw/.manifest.json`, and `HANDOFF.md`. Commit.

---

## Summary

After compilation, report to the user:
- Which sources were compiled
- How many pages were created vs updated
- Any failures or skipped files
- Current wiki stats (total pages by category)
