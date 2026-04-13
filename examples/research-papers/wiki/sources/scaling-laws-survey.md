---
title: "Neural Scaling Laws: A Comprehensive Survey"
type: source
source_file: "scaling-laws-survey.md"
source_type: md
full_source: "full-sources/scaling-laws-survey/"
date_ingested: 2026-04-13
key_entities:
  - "kaplan-jared"
  - "openai"
  - "google-deepmind"
key_concepts:
  - "scaling-laws"
  - "compute-optimal-training"
source_refs: []
created: 2026-04-13
updated: 2026-04-13
tags:
  - "scaling"
  - "training"
  - "compute"
---

## Overview

A comprehensive survey examining the empirical and theoretical foundations of neural scaling laws. Traces the development from Kaplan et al.'s (2020) foundational power-law characterizations at OpenAI to Hoffmann et al.'s (2022) compute-optimal training paradigm (Chinchilla) at Google DeepMind.

## Key Claims

- Test loss follows smooth power-law relationships as a function of model size (N), dataset size (D), and compute (C), when other factors are not bottlenecked.
- **Kaplan et al. (2020):** Model size is more important than dataset size for a fixed compute budget. Recommended N ∝ C^(0.73).
- **Hoffmann et al. (2022) — Chinchilla:** Model parameters and training tokens should scale approximately equally. Optimal training tokens ≈ 20× model parameters. This contradicted Kaplan's recommendation.
- Chinchilla (70B params, 1.4T tokens) outperformed Gopher (280B params, 300B tokens) despite being 4× smaller, validating compute-optimal training.

## Evidence/Data

- Kaplan: experiments spanning 768 to 1.5B parameters, 22M to 23B tokens.
- Hoffmann: 400+ training runs, 70M to 16B parameters, 5B to 500B tokens.
- Three complementary analytical approaches in Chinchilla (fixed compute, IsoFLOP, parametric fitting) all converged on the same result.

## Limitations

- Original scaling laws characterize pre-training loss, not downstream task performance.
- Did not address multimodal scaling, data quality effects, or inference-time compute scaling.
- Relationship between scaling and architectural choices (e.g., attention variants) only briefly touched.

## Cross-References

- [OpenAI](../entities/openai.md) — organization behind the Kaplan et al. scaling laws [STATED]
- [Google DeepMind](../entities/google-deepmind.md) — organization behind Chinchilla [STATED]
- [Jared Kaplan](../entities/kaplan-jared.md) — lead author of foundational scaling laws paper [STATED]
- [Ashish Vaswani](../entities/vaswani-ashish.md) — referenced for transformer architecture [STATED]

## See Also

- [Scaling Laws](../concepts/scaling-laws.md) [STATED]
- [Compute-Optimal Training](../concepts/compute-optimal-training.md) [STATED]
- [Attention Mechanisms](../concepts/attention-mechanisms.md) [INFERRED]
