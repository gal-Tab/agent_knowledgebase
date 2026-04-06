# LLM Wiki Agent

A Claude Code plugin that gives your agent persistent, structured memory. Drop PDFs, markdown files, or git repos into a folder — the agent extracts, compiles, and maintains a structured wiki. Ask domain questions and get answers grounded in your sources, with cross-references and citations.

## Install

**Prerequisites:** [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed and working.

```bash
# Install the plugin
claude plugin add /path/to/llm-wiki-agent

# In any project, initialize a knowledge base
/kb-init
```

**Optional dependencies** (checked by `/kb-init`):
- `pymupdf4llm` — for PDF ingestion: `pip3 install --user pymupdf4llm`
- `repomix` — for repo ingestion: `npm install -g repomix` (npx fallback available)

## Usage

**Two human actions.** Everything else is automatic.

### 1. Drop files into `raw/`

```bash
cp ~/papers/interesting-paper.pdf raw/
cp ~/notes/meeting-notes.md raw/
```

### 2. Start a session and compile

```bash
claude
# Agent detects new files automatically on session start
# Say "compile" or use /kb-compile to process them
```

### 3. Ask questions

Ask domain questions — the agent consults the wiki first, citing your sources:

> "What does the paper say about scaling laws?"
> "Compare the architectures described in these two papers"
> "What do we know about OpenAI's approach to training?"

The agent reads the wiki index, identifies relevant pages, and synthesizes answers with source citations.

## What You Get Per Project

After running `/kb-init`, your project gets:

```
project/
├── raw/                       # Drop files here
│   ├── .manifest.json         # Pipeline state (auto-managed)
│   └── .extracted/            # Extracted markdown (auto-generated)
├── wiki/                      # Compiled wiki (auto-managed)
│   ├── index.md               # Content catalog
│   ├── sources/               # One summary per raw source
│   ├── entities/              # People, orgs, products, tools
│   ├── concepts/              # Ideas, frameworks, definitions
│   └── comparisons/           # Cross-source analysis
├── tools/
│   ├── extract-pdf.py         # PDF → markdown
│   └── extract-repo.sh        # Repo → markdown
├── wiki-schema.md             # Domain rules (customize this!)
└── HANDOFF.md                 # Session persistence
```

Each project has its own isolated knowledge base. The plugin provides the engine; your project owns the data.

## How Compilation Works

**Two-phase process:**

1. **Source page** — Agent reads extracted markdown, creates `wiki/sources/{slug}.md` with structured summary, and lists candidate entities/concepts
2. **Resolution** — For each candidate, agent checks the wiki index. Existing pages get updated. New pages are created if they meet the thresholds in `wiki-schema.md`. Index is updated, git commits track everything.

**Thresholds** (configurable in `wiki-schema.md`):
- **Entities:** Created if central to a source's thesis or mentioned in 2+ sources
- **Concepts:** Only domain-specific or novel concepts (not common knowledge)
- **Comparisons:** Only on explicit request or when sources clearly contradict

## Customizing for Your Domain

Edit `wiki-schema.md` after running `/kb-init`. The most important part is the **Domain Description** — it tells the agent what counts as "common knowledge" vs worth a dedicated page.

Example for ML research:
```markdown
## Domain Description
Machine learning research. Covers model architectures, training techniques,
scaling laws, and benchmark results.
```

You can also customize entity types, page sections, creation thresholds, and compilation rules.

## Commands

| Command | What it does |
|---------|-------------|
| `/kb-init` | Initialize a knowledge base in the current project |
| `/kb-compile` | Compile new or updated files from raw/ into wiki pages |

The `kb-query` skill auto-invokes when you ask domain questions — no command needed.

## Supported Formats

| Format | Tool | Status |
|--------|------|--------|
| PDF | pymupdf4llm | Supported |
| Markdown / Text | passthrough | Supported |
| Git repos | repomix | Supported |

Adding a format = one extraction script + one line in the compile command.

## Architecture

```
Plugin (shared)          →  Project (per-project)
  hooks/kb-status             raw/ + wiki/ + manifest
  commands/kb-compile         wiki-schema.md
  skills/kb-query             HANDOFF.md
  tools/extract-*             tools/ (copied by kb-init)
```

The plugin fires hooks on every session start and user prompt. In projects without a KB (no `raw/` directory), the hook exits silently with zero overhead.

## Scaling

| Wiki Size | Strategy |
|-----------|----------|
| 0-100 pages | Flat `index.md` |
| 100-300 pages | Category sub-indexes |
| 300+ pages | grep-based search |

## Inspired By

- [Karpathy's LLM Knowledge Bases](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [Cole Medin](https://github.com/cole-medin) — git-as-memory
- [CandleKeep](https://getcandlekeep.com) — auto-detection model

## License

MIT
