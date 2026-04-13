---
title: "Jared Kaplan"
type: entity
aliases:
  - "Kaplan"
  - "J. Kaplan"
source_refs:
  - slug: "scaling-laws-survey"
    confidence: STATED
  - slug: "efficient-inference"
    confidence: STATED
created: 2026-04-13
updated: 2026-04-13
tags:
  - "researcher"
  - "scaling-laws"
---

## Overview

Jared Kaplan is a researcher at OpenAI and Johns Hopkins University, known as the lead author of "Scaling Laws for Neural Language Models" (2020). This foundational work established the empirical framework for understanding how language model performance scales with model size, dataset size, and compute.

## Key Facts

- Lead author of "Scaling Laws for Neural Language Models" (Kaplan et al., 2020)
- Affiliated with OpenAI and Johns Hopkins University
- Characterized power-law relationships: L(N) ∝ N^(-0.076), L(D) ∝ D^(-0.095), L(C) ∝ C^(-0.050)
- Original analysis recommended scaling model size more aggressively than dataset size (N ∝ C^0.73) — later revised by Chinchilla

## Source Appearances

- [Neural Scaling Laws Survey](../sources/scaling-laws-survey.md) — central figure, lead author of the foundational scaling laws paper [STATED]
- [Efficient Inference](../sources/efficient-inference.md) — scaling laws inform model sizing decisions for deployment [STATED]

## See Also

- [OpenAI](../entities/openai.md) [STATED]
- [Scaling Laws](../concepts/scaling-laws.md) [STATED]
- [Compute-Optimal Training](../concepts/compute-optimal-training.md) [INFERRED]
