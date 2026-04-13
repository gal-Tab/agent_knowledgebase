---
title: "Attention Mechanisms in Transformer Architectures"
type: source
source_file: "attention-mechanisms.md"
source_type: md
full_source: "full-sources/attention-mechanisms/"
date_ingested: 2026-04-13
key_entities:
  - "vaswani-ashish"
  - "openai"
  - "google-deepmind"
key_concepts:
  - "attention-mechanisms"
  - "scaling-laws"
source_refs: []
created: 2026-04-13
updated: 2026-04-13
tags:
  - "attention"
  - "transformers"
  - "architecture"
---

## Overview

A survey of attention mechanisms from their introduction in the transformer architecture by Vaswani et al. (2017) at Google Brain to modern efficient variants. Covers scaled dot-product attention, multi-head self-attention, positional encoding, and the transition from recurrent to attention-based architectures.

## Key Claims

- Scaled dot-product attention (softmax(QK^T/√d_k)V) eliminates the sequential processing bottleneck of RNNs, enabling parallelized training.
- Multi-head attention allows the model to jointly attend to information from different representation subspaces — different heads learn syntactic, semantic, and positional patterns.
- Flash Attention achieves 2-4× speedup by computing attention in blocks via GPU SRAM tiling, reducing memory from O(n²) to O(n) without approximation.
- Grouped Query Attention (GQA) reduces KV-cache memory by sharing key-value projections within head groups, used in LLaMA 2 and Mistral.

## Evidence/Data

- The original transformer used h=8 attention heads with d_k=64. Modern LLMs (GPT-3) use 96 heads.
- Flash Attention 2 and 3 further optimized for newer hardware architectures.
- Linear attention variants (Performer, Linear Transformer) achieve O(n) complexity but with quality trade-offs.

## Limitations

- Focus on NLP applications; limited coverage of vision transformers and multimodal attention.
- Interaction between attention variants and scaling laws not deeply explored.

## Cross-References

- [Ashish Vaswani](../entities/vaswani-ashish.md) — lead author of "Attention Is All You Need" [STATED]
- [OpenAI](../entities/openai.md) — GPT series uses decoder-only transformers; Sparse Transformer from OpenAI [STATED]
- [Google DeepMind](../entities/google-deepmind.md) — Chinchilla study referenced for scaling interactions [STATED]

## See Also

- [Attention Mechanisms](../concepts/attention-mechanisms.md) [STATED]
- [Scaling Laws](../concepts/scaling-laws.md) [INFERRED]
- [Compute-Optimal Training](../concepts/compute-optimal-training.md) [INFERRED]
