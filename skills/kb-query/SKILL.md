---
name: kb-query
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

3. **Synthesize your answer** from wiki content, citing sources:
   - "According to [Source Title](wiki/sources/slug.md)..."
   - "The wiki notes that [Entity](wiki/entities/slug.md)..."

4. **Distinguish wiki knowledge from general knowledge.** If you also use general knowledge beyond the wiki, say so: "The wiki says X. Additionally, from general knowledge..."

## Guardrails

- **Never load the entire wiki into context.** Always read the index first, then only the relevant pages.
- **Never read more than 5 pages per query** unless the user explicitly asks for a comprehensive review.
- **Always cite sources.** Every claim from the wiki should link to the page it came from.

## File-Back (Compounding Loop)

After producing an answer that synthesizes new cross-references or insights not already captured in the wiki:

1. Suggest: "This answer contains insights not yet in the wiki. Want me to file it back?"
2. If the user agrees, create the appropriate wiki page:
   - **Comparison page** if the answer compares entities/concepts across sources
   - **Concept page** if the answer defines or refines a concept
   - **Entity update** if the answer reveals new facts about an existing entity
3. Update `wiki/index.md` with the new page
4. Git commit: `[query-file] Filed: {title}`
