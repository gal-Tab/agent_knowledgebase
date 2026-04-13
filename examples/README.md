# LLM Wiki Agent — Worked Example

This directory contains a complete end-to-end example of the LLM Wiki Agent pipeline.

## Directory Structure

```
examples/research-papers/
├── raw/                              # Source files (input)
│   ├── scaling-laws-survey.md        # ~2000 word survey on neural scaling laws
│   ├── attention-mechanisms.md       # ~1500 word paper on attention in transformers
│   └── efficient-inference.md        # ~1500 word paper on inference optimization
│
└── wiki/                             # Compiled wiki output (generated)
    ├── index.md                      # Content catalog
    ├── sources/                      # One summary per source file
    ├── entities/                     # People, organizations
    ├── concepts/                     # Ideas, frameworks
    └── comparisons/                  # Cross-source analysis
```

## What This Demonstrates

The three synthetic papers share overlapping entities and concepts:

| Entity/Concept | scaling-laws-survey | attention-mechanisms | efficient-inference |
|----------------|:-------------------:|:--------------------:|:-------------------:|
| OpenAI         | ✓                   | ✓                    | ✓                   |
| Google DeepMind| ✓                   | ✓                    | ✓                   |
| Vaswani et al. | ✓                   | ✓                    | ✓                   |
| Kaplan et al.  | ✓                   | —                    | ✓                   |
| Scaling Laws   | ✓                   | ✓                    | ✓                   |
| Attention      | ✓                   | ✓                    | ✓                   |
| Compute-Optimal| ✓                   | —                    | ✓                   |

This overlap demonstrates cross-source linking: entities and concepts that appear in multiple sources get their own wiki pages with references back to each source.

## How to Reproduce

1. Install the LLM Wiki Agent plugin
2. Navigate to this directory: `cd examples/research-papers`
3. Initialize the knowledge base: `/kb-init`
4. Compile the sources: `/kb-compile`

The compiled wiki/ output is committed to this repo so you can inspect it without running the pipeline.
