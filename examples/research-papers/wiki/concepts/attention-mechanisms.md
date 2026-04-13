---
title: "Attention Mechanisms"
type: concept
aliases:
  - "self-attention"
  - "multi-head attention"
  - "scaled dot-product attention"
domain_tags:
  - "machine-learning"
  - "architecture"
  - "transformers"
source_refs:
  - slug: "attention-mechanisms"
    confidence: STATED
  - slug: "efficient-inference"
    confidence: STATED
  - slug: "scaling-laws-survey"
    confidence: INFERRED
created: 2026-04-13
updated: 2026-04-13
tags:
  - "foundational"
  - "architecture"
---

## Definition

Attention mechanisms are the core computational building block of transformer architectures. Scaled dot-product attention computes: Attention(Q, K, V) = softmax(QK^T / √d_k) V, where Q (queries), K (keys), and V (values) enable each position in a sequence to directly access information from every other position. Multi-head attention extends this by projecting Q, K, V into h separate subspaces and concatenating the results, allowing the model to attend to different types of relationships simultaneously.

## Context

Introduced by Ashish Vaswani et al. (2017) at Google Brain in "Attention Is All You Need." The key innovation was eliminating recurrence entirely, replacing RNN/LSTM sequential processing with parallel attention computation. This enabled both better long-range dependency modeling (avoiding vanishing gradients) and efficient GPU parallelization during training.

Standard self-attention has O(n²) complexity in sequence length, creating a bottleneck for long contexts. Flash Attention (Dao et al., 2022) addresses this via GPU SRAM tiling, reducing memory from O(n²) to O(n) without approximation. Grouped Query Attention (GQA) reduces KV-cache memory by sharing key-value projections across head groups.

The interaction between attention variants and scaling laws remains an active research area — preliminary evidence suggests power-law scaling exponents are robust to attention mechanism changes, consistent with Kaplan et al.'s observation that scaling laws are relatively architecture-independent.

## Related Concepts

- [Scaling Laws](../concepts/scaling-laws.md) — scaling behavior may vary with attention variants; attention enables the model scale that scaling laws characterize
- [Compute-Optimal Training](../concepts/compute-optimal-training.md) — efficient attention effectively increases "useful compute," potentially shifting compute-optimal boundaries [INFERRED]

## See Also

- [Ashish Vaswani](../entities/vaswani-ashish.md) [STATED]
- [Google DeepMind](../entities/google-deepmind.md) [STATED]
- [OpenAI](../entities/openai.md) [INFERRED]
- [Scaling Laws](../concepts/scaling-laws.md) [INFERRED]
