---
description: Initialize a knowledge base in the current project. Creates raw/, wiki/, wiki-schema.md, and extraction tools.
allowed-tools: Bash(mkdir:*), Bash(cp:*), Bash(chmod:*), Bash(python3:*), Bash(command:*), Write, Read, Glob
---

# Initialize Knowledge Base

Set up a knowledge base in the current project so Claude can ingest source files and maintain a compiled wiki.

## Step 1: Check for Existing KB

Check if `raw/` already exists in the project root.

- If it exists, tell the user: "A knowledge base already exists in this project. Existing data will not be overwritten. Proceeding to verify structure."
- If it does not exist, proceed normally.

## Step 2: Create Directory Structure

```bash
mkdir -p raw/.extracted
mkdir -p wiki/sources wiki/entities wiki/concepts wiki/comparisons
mkdir -p tools
```

## Step 3: Initialize State Files

Create `raw/.manifest.json` with content `{}` (only if it doesn't already exist).

Create `wiki/index.md` with this content (only if it doesn't already exist):

```markdown
# Wiki Index
Updated: (not yet populated) | Total: 0 pages

## Sources (0)

## Entities (0)

## Concepts (0)

## Comparisons (0)
```

Create `HANDOFF.md` (only if it doesn't already exist) by copying the template at `${CLAUDE_PLUGIN_ROOT}/templates/handoff.md`. Read it and write it to `./HANDOFF.md`.

## Step 4: Copy Wiki Schema

Copy the wiki schema template into the project root as `wiki-schema.md` (only if it doesn't already exist).

The template is at `${CLAUDE_PLUGIN_ROOT}/templates/wiki-schema.md`. Read it and write it to `./wiki-schema.md`.

Tell the user: **"Edit wiki-schema.md to describe your domain. A good domain description dramatically improves compilation quality."**

## Step 5: Copy Extraction Tools

Copy these files from the plugin into the project's `tools/` directory:

- `${CLAUDE_PLUGIN_ROOT}/tools/extract-pdf.py` → `./tools/extract-pdf.py`
- `${CLAUDE_PLUGIN_ROOT}/tools/extract-repo.sh` → `./tools/extract-repo.sh`

Make them executable:
```bash
chmod +x tools/extract-pdf.py tools/extract-repo.sh
```

## Step 6: Update .gitignore

Append these lines to `.gitignore` if they are not already present:

```
# Knowledge base — extracted files (regenerated from raw sources)
raw/.extracted/

# Knowledge base — binary source files (avoid bloating git history)
raw/*.pdf
raw/*.epub
raw/*.docx
raw/*.xlsx
raw/*.pptx
```

## Step 7: Check Dependencies

Run these checks and report results:

```bash
python3 -c "import pymupdf4llm; print('pymupdf4llm: OK')" 2>/dev/null || echo "pymupdf4llm: MISSING — run: pip3 install --user pymupdf4llm"
```

```bash
command -v repomix &>/dev/null && echo "repomix: OK" || echo "repomix: MISSING — run: npm install -g repomix (or npx will be used as fallback)"
```

## Step 8: Report to User

Summarize what was created and give next steps:

```
Knowledge base initialized:
  raw/           — drop source files here (PDF, markdown, text)
  wiki/          — compiled wiki pages (managed by agent)
  wiki-schema.md — domain rules (customize this!)
  tools/         — extraction scripts
  HANDOFF.md     — session persistence

Next steps:
  1. Edit wiki-schema.md to describe your domain
  2. Drop files into raw/
  3. Start a new session or say "compile the new files"
```

If any dependencies are missing, list them with install commands.
