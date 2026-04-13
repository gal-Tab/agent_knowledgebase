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
  - "scaling-laws-neural-lm"
created: 2026-04-01
updated: 2026-04-01
tags:
  - "foundational"
---

## Definition

Scaling laws describe the empirical power-law relationships between neural network performance (typically measured by test loss) and key scaling factors: model size (parameters), dataset size (tokens), and compute budget (FLOPs).

## Context

First systematically characterized by Kaplan et al. (2020) at OpenAI, scaling laws have become a foundational tool for predicting model performance and allocating training compute efficiently. The Chinchilla study by Hoffmann et al. (2022) at Google DeepMind refined the optimal allocation ratio.

## Related Concepts

- [Compute-Optimal Training](../concepts/compute-optimal-training.md) — the optimal allocation of compute between model size and data
- [Attention Mechanisms](../concepts/attention-mechanisms.md) — the architectural foundation that enables scaling

## See Also

- [Jared Kaplan](../entities/kaplan-jared.md)
- [OpenAI](../entities/openai.md)
