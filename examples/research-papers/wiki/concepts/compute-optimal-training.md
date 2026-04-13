---
title: "Compute-Optimal Training"
type: concept
aliases:
  - "Chinchilla-optimal"
  - "compute-optimal"
domain_tags:
  - "machine-learning"
  - "training"
  - "efficiency"
source_refs:
  - slug: "scaling-laws-survey"
    confidence: STATED
  - slug: "efficient-inference"
    confidence: STATED
created: 2026-04-13
updated: 2026-04-13
tags:
  - "foundational"
  - "training-strategy"
---

## Definition

Compute-optimal training refers to the principle of allocating a fixed compute budget between model size and training data in a way that minimizes test loss. Established by Hoffmann et al. (2022) in the Chinchilla study at Google DeepMind, the key finding is that model parameters (N) and training tokens (D) should scale approximately equally with compute budget (C): N_opt ∝ C^0.50, D_opt ∝ C^0.50. The practical rule of thumb is that optimal training tokens ≈ 20× model parameters.

## Context

This concept emerged from the Chinchilla paper's revision of earlier scaling law prescriptions by Kaplan et al. (2020), who had recommended scaling model size more aggressively (N ∝ C^0.73). The demonstration that Chinchilla (70B params, 1.4T tokens) outperformed the 4× larger Gopher (280B params, 300B tokens) proved that many existing LLMs were significantly undertrained.

The concept has implications beyond training — for inference optimization, training larger-than-needed models following Chinchilla-optimal recipes and then applying post-training quantization may achieve better quality-per-inference-FLOP than training smaller models natively.

## Related Concepts

- [Scaling Laws](../concepts/scaling-laws.md) — the empirical framework from which compute-optimal prescriptions are derived
- [Attention Mechanisms](../concepts/attention-mechanisms.md) — efficient attention may shift compute-optimal boundaries by reducing overhead [INFERRED]

## See Also

- [Google DeepMind](../entities/google-deepmind.md) [STATED]
- [Jared Kaplan](../entities/kaplan-jared.md) [INFERRED]
- [OpenAI](../entities/openai.md) [INFERRED]
- [Scaling Laws](../concepts/scaling-laws.md) [STATED]
