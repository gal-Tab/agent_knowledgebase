---
name: wiki-query
description: Use when user asks domain questions and a wiki/ directory exists in the project, when user references "my research" or "what I've read," when user asks about topics that could be in their knowledge base, or when user asks to compare entities from ingested sources
allowed-tools: Read, Glob, Grep, Write, Edit, Bash(git add:*), Bash(git commit:*), Bash(git status:*)
---

# Knowledge Base Query

Consult the project's compiled wiki to answer domain questions with source citations.

## When to Use This Skill

- User asks about topics matching wiki entity/concept names
- User asks for comparisons between subjects in the wiki
- User references "my research," "what I've read," "based on what we know"
- User asks questions in the domain described by wiki-schema.md

## When NOT to Use This Skill

- Pure coding questions unrelated to domain knowledge
- General knowledge the user isn't asking you to verify against sources
- Meta questions about the wiki itself ("how many pages?") — just check the filesystem
- Questions you can answer without domain context

## Query Procedure

1. **Read `wiki/index.md`** to identify 2-5 relevant pages. If total pages exceed 100, read the relevant category sub-index instead. If pages exceed 300, use `grep -rl "search term" wiki/` to discover relevant pages first.

2. **Read those pages** (maximum 5 per query unless the user explicitly asks for comprehensive review).

3. **Consult compound learnings (cheap, index-first).** If a learnings store exists, grep its compact index for tags matching the question — both tiers (`grep -i "<term>" .compound/index.md "$COMPOUND_KNOWLEDGE_HOME/index.md" ~/.claude/compound-knowledge/index.md 2>/dev/null`). The index is headline-only, so this is ~one grep. If a relevant **correction or playbook** headline matches, surface it; read its body (`<root>/<type-dir>/<id>.md`) **only if it sharpens the answer**. Any body you open counts toward the 5-read cap. Most queries match nothing here and pay only the grep.

4. **Synthesize your answer** from wiki content, citing sources:
   - "According to [Source Title](wiki/sources/slug.md)..."
   - "The wiki notes that [Entity](wiki/entities/slug.md)..."
   - If a learning informed the answer, cite its id + scope: "A past correction (`kw-…`, project) also warns…"

5. **Distinguish wiki knowledge from general knowledge.** If you also use general knowledge beyond the wiki, say so: "The wiki says X. Additionally, from general knowledge..."

> **Router note:** this step is a *cheap consult* of the agent's own lessons alongside a domain answer. For a question that is purely about past lessons ("what did we learn about X", "have we hit this before"), use the **`learn-recall`** skill instead — it merges both tiers and reads bodies on demand without the wiki round-trip.

## Deep Cite Mode (Source Preservation)

When a wiki summary page is insufficient to answer a question with the detail or precision required — or when the user asks for exact quotes, specific sections, or verbatim text — use the full-source preservation layer:

1. Check if the source page has `full_source:` in its frontmatter
2. If yes, read `wiki/full-sources/{slug}/toc.md` to see the original document structure
3. Identify the relevant page(s) from the table of contents
4. Read the specific `wiki/full-sources/{slug}/page-{N}.md` file(s)
5. Quote original text directly, citing the specific page: "From [Source Title, Page N](wiki/full-sources/{slug}/page-{N}.md)..."

**When to use deep cite:**
- User asks for exact quotes or verbatim text
- User needs more detail than the summary provides
- User asks "what exactly does the source say about..."
- The summary is ambiguous and the original text would clarify

**When NOT to use deep cite:**
- The summary page sufficiently answers the question
- The user is asking for a high-level overview
- No `full_source:` field exists in the source page frontmatter

## Guardrails

- **Never load the entire wiki into context.** Always read the index first, then only the relevant pages.
- **Never read more than 5 pages per query** unless the user explicitly asks for a comprehensive review.
- **Always cite sources.** Every claim from the wiki should link to the page it came from.
- **Deep cite pages count toward the 5-page limit.** Each full-source page-{N}.md counts as one page read.

## File-Back (Compounding Loop)

After producing an answer that synthesizes new cross-references or insights not already captured in the wiki:

1. Suggest: "This answer contains insights not yet in the wiki. Want me to file it back?"
2. If the user agrees, create the appropriate wiki page:
   - **Comparison page** if the answer compares entities/concepts across sources
   - **Concept page** if the answer defines or refines a concept
   - **Entity update** if the answer reveals new facts about an existing entity
3. Update `wiki/index.md` with the new page
4. Git commit: `[query-file] Filed: {title}`
