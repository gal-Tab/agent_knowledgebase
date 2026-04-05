# Wiki Schema

## Domain Description

General-purpose knowledge base. Covers any domain the user feeds it.
Customize this file per project to specialize compilation rules, entity types, and thresholds.

## Page Types

### source
Frontmatter: title, source_file, source_type (pdf|md|repo|html|epub), date_ingested, key_entities[], key_concepts[]
Sections: Overview, Key Claims, Evidence/Data, Limitations, Cross-References
Max length: 1500 words. Longer sources should be summarized more aggressively.

### entity
Frontmatter: title, type (person|org|product|place|tool|project), aliases[], source_refs[]
Sections: Overview, Key Facts, Source Appearances
Merge threshold: Create if central to any source OR mentioned in 2+ sources.
When updating: append new source appearances, update Key Facts if new info contradicts or extends.

### concept
Frontmatter: title, aliases[], domain_tags[], source_refs[]
Sections: Definition, Context, Related Concepts
Create threshold: Only if domain-specific or novel. Skip widely-known general concepts.
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

## Link Format

Use standard markdown links with relative paths:
```
[Display Text](../category/slug.md)
```

Every page must end with a `## See Also` section listing related pages as backlinks.

## Compilation Rules

- One source summary per raw file, always created
- Entity pages: create if central to a source OR mentioned in 2+ existing sources
- Concept pages: only for domain-specific or novel concepts (skip common knowledge like "machine learning" unless the source offers a unique perspective)
- Comparison pages: only on explicit user request or when sources clearly conflict
- When updating an existing page with info from a new source: append to relevant sections, don't rewrite existing content
- Flag contradictions inline: **[Contradiction]** Source A claims X, but Source B claims Y
- Slug format: lowercase, hyphens, no special characters (e.g., `openai`, `scaling-laws`, `kaplan-jared`)
