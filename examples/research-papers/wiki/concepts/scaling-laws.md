---
title: "Scaling Laws"
type: concept
aliases:
  - "neural scaling laws"
  - "power-law scaling"
domain_tags:
  - "machine-learning"
  - "training"
source_refs:
  - slug: "scaling-laws-survey"
    confidence: STATED
  - slug: "attention-mechanisms"
    confidence: INFERRED
  - slug: "efficient-inference"
    confidence: STATED
created: 2026-04-13
updated: 2026-04-13
tags:
  - "foundational"
---

## Definition

Scaling laws describe the empirical power-law relationships between neural network performance (typically measured by test loss) and key scaling factors: model size (parameters N), dataset size (tokens D), and compute budget (FLOPs C). When other factors are not bottlenecked, test loss follows smooth, predictable curves over many orders of magnitude.

Key relationships established by Kaplan et al. (2020):
- L(N) ∝ N^(-0.076)
- L(D) ∝ D^(-0.095)
- L(C) ∝ C^(-0.050)

## Context

First systematically characterized by Jared Kaplan and colleagues at OpenAI in January 2020. The initial analysis suggested scaling model size more aggressively than dataset size (N ∝ C^0.73). This was significantly revised by the Chinchilla study (Hoffmann et al., 2022) at Google DeepMind, which demonstrated that parameters and tokens should scale approximately equally (both ∝ C^0.50), with optimal training tokens ≈ 20× parameters.

The scaling laws have direct economic implications: the difference between Kaplan-optimal and Chinchilla-optimal compute allocation can determine whether a model leads benchmarks or underperforms models a fraction of its size. This paradigm shift influenced Meta's LLaMA models and subsequent training strategies across the industry.

## Related Concepts

- [Compute-Optimal Training](../concepts/compute-optimal-training.md) — the optimal allocation of compute derived from scaling law analysis
- [Attention Mechanisms](../concepts/attention-mechanisms.md) — the architectural foundation that enables scaling; scaling exponents may vary with attention variants

## See Also

- [Jared Kaplan](../entities/kaplan-jared.md) [STATED]
- [OpenAI](../entities/openai.md) [STATED]
- [Google DeepMind](../entities/google-deepmind.md) [STATED]
- [Compute-Optimal Training](../concepts/compute-optimal-training.md) [STATED]
