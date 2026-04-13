---
title: "Scaling Laws for Neural Language Models"
type: source
source_file: "scaling-laws-survey.pdf"
source_type: pdf
key_entities:
  - "kaplan-jared"
  - "openai"
key_concepts:
  - "scaling-laws"
  - "compute-optimal-training"
source_refs: []
created: 2026-04-01
updated: 2026-04-01
tags:
  - "machine-learning"
  - "scaling"
---

## Overview

This paper by Kaplan et al. at OpenAI characterizes the power-law relationships between model performance and scale factors (parameters, data, compute).

## Key Claims

- Test loss follows smooth power-law relationships with model size, dataset size, and compute.
- Model size is the most important factor for a fixed compute budget.
- These scaling laws hold over many orders of magnitude.

## Evidence/Data

Experiments spanning models from 768 to 1.5 billion parameters, trained on 22 million to 23 billion tokens.

## Limitations

- Focused on autoregressive language models only.
- Did not explore compute-optimal allocation as thoroughly as later work (Chinchilla).

## Cross-References

- [OpenAI](../entities/openai.md) — the organization that produced this research
- [Jared Kaplan](../entities/kaplan-jared.md) — lead author

## See Also

- [Compute-Optimal Training](../concepts/compute-optimal-training.md)
- [Scaling Laws](../concepts/scaling-laws.md)
