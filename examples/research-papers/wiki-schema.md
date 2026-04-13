# Wiki Schema

## Domain Description

Machine learning research. Covers model architectures, training techniques, scaling laws, benchmark results, and inference optimization for large language models.

## Page Types

### source
Frontmatter: title, source_file, source_type (pdf|md|repo|html|epub), date_ingested, key_entities[], key_concepts[]
Sections: Overview, Key Claims, Evidence/Data, Limitations, Cross-References
Max length: 1500 words. Longer sources should be summarized more aggressively.

### entity
Frontmatter: title, type (person|org|product|place|tool|project), aliases[], source_refs[]
Sections: Overview, Key Facts, Source Appearances
Merge threshold: Create if central to any source's thesis OR mentioned in 2+ existing sources.
When updating: append new source appearances, update Key Facts if new info contradicts or extends.

### concept
Frontmatter: title, aliases[], domain_tags[], source_refs[]
Sections: Definition, Context, Related Concepts
Create threshold: Only if domain-specific or novel. Skip concepts that an ML practitioner would already know.
When updating: refine definition with new perspectives, add cross-references.

### comparison
Frontmatter: title, compared_entities[], source_refs[]
Sections: Overview, Dimensions of Comparison, Summary Table, Synthesis
Create threshold: Only when explicitly requested by user, or when 2+ sources offer clearly conflicting claims about the same topic.

## Confidence Labels

Every cross-reference between wiki pages must include a confidence label.

| Label | Meaning | Example |
|-------|---------|---------|
| STATED | Explicitly stated in source text | "Vaswani works at Google" |
| INFERRED | Reasonable deduction from context | Co-authors → collaboration |
| UNCERTAIN | Flagged for human review | Ambiguous attribution |

## Frontmatter Template

```yaml
---
title: ""
type: source|entity|concept|comparison
source_refs:
  - slug: ""
    confidence: STATED|INFERRED|UNCERTAIN
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
| entity (person) | `{lastname}-{firstname}` | `kaplan-jared` |
| entity (org) | Lowercase hyphenated name | `openai` |
| concept | Lowercase hyphenated name | `scaling-laws` |

## Link Format

Use standard markdown links with relative paths:
```
[Display Text](../category/slug.md)
```

Every page must end with a `## See Also` section listing related pages as backlinks with confidence labels.

## Compilation Rules

- One source summary per raw file, always created
- Entity pages: create if central to a source's thesis OR mentioned in 2+ existing sources
- Concept pages: only for domain-specific or novel concepts
- When updating: append, don't rewrite. Flag contradictions inline.
