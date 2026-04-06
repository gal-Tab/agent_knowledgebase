# Wiki Schema

## Domain Description

<!-- CUSTOMIZE THIS: Describe what this knowledge base covers in 2-3 sentences.
     A good domain description dramatically improves compilation quality by helping
     the agent decide which concepts are "common knowledge" vs worth a dedicated page.

     Examples:
       "Investment research focused on SaaS companies. Covers financial metrics,
        competitive analysis, and market trends for B2B software businesses."
       "Machine learning research. Covers model architectures, training techniques,
        scaling laws, and benchmark results."
       "Internal engineering documentation for the Acme platform. Covers system
        architecture, API design, deployment procedures, and incident history."
-->

General-purpose knowledge base. Covers any domain the user feeds it.

## Page Types

### source
Frontmatter: title, source_file, source_type (pdf|md|repo|html|epub), date_ingested, key_entities[], key_concepts[]
Sections: Overview, Key Claims, Evidence/Data, Limitations, Cross-References
Max length: 1500 words. Longer sources should be summarized more aggressively.

### entity
Frontmatter: title, type (person|org|product|place|tool|project), aliases[], source_refs[]
Sections: Overview, Key Facts, Source Appearances
Merge threshold: Create if central to any source's thesis OR mentioned in 2+ existing sources. For multi-author papers, create pages only for the first author and any co-authors who are independently notable in the domain (max 3). Other authors appear as mentions in the source page only.
When updating: append new source appearances, update Key Facts if new info contradicts or extends.

### concept
Frontmatter: title, aliases[], domain_tags[], source_refs[]
Sections: Definition, Context, Related Concepts
Create threshold: Only if domain-specific or novel. Skip concepts that a practitioner in the domain described above would already know. If the domain description is general-purpose, only create pages for concepts that are coined, defined, or given novel treatment by the source.
When updating: refine definition with new perspectives, add cross-references.

### comparison
Frontmatter: title, compared_entities[], source_refs[]
Sections: Overview, Dimensions of Comparison, Summary Table, Synthesis
Create threshold: Only when explicitly requested by user, or when 2+ sources offer clearly conflicting claims about the same topic.

## Frontmatter Template

```yaml
---
title: ""
type: source|entity|concept|comparison
source_refs: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: []
---
```

## Slug Rules

All slugs are lowercase, hyphens only, no special characters.

| Page type | Slug derivation | Example |
|-----------|-----------------|---------|
| source (paper) | Abbreviated title | `scaling-laws-neural-lm` |
| source (book) | `{author-lastname}-{short-title}` | `goodfellow-deep-learning` |
| source (repo) | Repo name | `my-tool` |
| source (doc) | Descriptive short name | `company-overview` |
| entity (person) | `{lastname}-{firstname}` | `kaplan-jared` |
| entity (org) | Lowercase hyphenated name | `openai` |
| concept | Lowercase hyphenated name | `scaling-laws` |
| comparison | `{topic}-comparison` | `gpt4-vs-claude-comparison` |

## Link Format

Use standard markdown links with relative paths:
```
[Display Text](../category/slug.md)
```

Every page must end with a `## See Also` section listing related pages as backlinks.

## Compilation Rules

- One source summary per raw file, always created
- Entity pages: create if central to a source's thesis OR mentioned in 2+ existing sources
- Concept pages: only for domain-specific or novel concepts
- Comparison pages: only on explicit user request or when sources clearly conflict
- When updating an existing page with info from a new source: append to relevant sections, don't rewrite existing content
- Flag contradictions inline: **[Contradiction]** Source A claims X, but Source B claims Y
