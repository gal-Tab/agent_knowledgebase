---
title: "Google DeepMind"
type: entity
aliases:
  - "DeepMind"
  - "Google Brain"
source_refs:
  - slug: "scaling-laws-survey"
    confidence: STATED
  - slug: "attention-mechanisms"
    confidence: STATED
  - slug: "efficient-inference"
    confidence: STATED
created: 2026-04-13
updated: 2026-04-13
tags:
  - "organization"
  - "ai-lab"
---

## Overview

Google DeepMind (formerly separate entities Google Brain and DeepMind) is an AI research lab that has made major contributions to transformer architectures, scaling law research, and hardware optimization for AI. Notable for the Chinchilla study that reshaped compute-optimal training practices.

## Key Facts

- Google Brain team (later merged into DeepMind) created the transformer architecture via Vaswani et al. (2017)
- Published "Training Compute-Optimal Large Language Models" (Hoffmann et al., 2022) — the Chinchilla paper
- Chinchilla (70B params) outperformed the larger Gopher model (280B params) by training on more data
- Developed TPU hardware architecture optimized for transformer inference workloads
- Trained Gopher (280B parameters) and PaLM language models

## Source Appearances

- [Neural Scaling Laws Survey](../sources/scaling-laws-survey.md) — Chinchilla study fundamentally revised compute-optimal training [STATED]
- [Attention Mechanisms](../sources/attention-mechanisms.md) — Google Brain created the original transformer; Chinchilla referenced for scaling interactions [STATED]
- [Efficient Inference](../sources/efficient-inference.md) — TPU optimization and Chinchilla implications for inference strategy [STATED]

## See Also

- [Ashish Vaswani](../entities/vaswani-ashish.md) [STATED]
- [OpenAI](../entities/openai.md) [INFERRED]
- [Scaling Laws](../concepts/scaling-laws.md) [STATED]
- [Compute-Optimal Training](../concepts/compute-optimal-training.md) [STATED]
- [Attention Mechanisms](../concepts/attention-mechanisms.md) [STATED]
