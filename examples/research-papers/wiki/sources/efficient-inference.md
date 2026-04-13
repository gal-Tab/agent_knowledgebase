---
title: "Efficient Inference for Large Language Models"
type: source
source_file: "efficient-inference.md"
source_type: md
full_source: "full-sources/efficient-inference/"
date_ingested: 2026-04-13
key_entities:
  - "openai"
  - "google-deepmind"
key_concepts:
  - "scaling-laws"
  - "attention-mechanisms"
  - "compute-optimal-training"
source_refs: []
created: 2026-04-13
updated: 2026-04-13
tags:
  - "inference"
  - "optimization"
  - "quantization"
  - "deployment"
---

## Overview

A survey of techniques for efficient LLM inference: quantization (GPTQ, AWQ), knowledge distillation, KV-cache optimization (PagedAttention, GQA), speculative decoding, and model pruning (SparseGPT, MoE). Examines how each technique interacts with the transformer attention mechanism and scaling laws.

## Key Claims

- Memory bandwidth, not compute, is the primary bottleneck for autoregressive LLM inference. Quantization directly improves throughput by reducing bytes per parameter.
- GPTQ uses approximate second-order information for 3-4 bit quantization with minimal quality loss. AWQ identifies "salient" weights for selective protection.
- Speculative decoding uses a small draft model to generate candidates verified by the large model in parallel, achieving 2-3× speedup with zero quality loss.
- A larger model aggressively quantized often outperforms a smaller model at full precision — consistent with scaling law predictions about the importance of original model capacity.
- Compute-optimal training (Chinchilla) combined with post-training quantization may achieve better quality-per-inference-FLOP than training smaller models natively.

## Evidence/Data

- LLaMA-70B KV-cache for a 4096-token sequence: ~5GB in FP16.
- Speculative decoding acceptance rates of 70-90% for well-chosen draft models.
- SparseGPT achieves 50-60% unstructured sparsity in one shot without retraining.
- Mixtral: 46.7B total parameters, 12.9B active per token via 8-expert MoE.

## Limitations

- Interaction between multiple techniques (e.g., quantization + speculative decoding) not well studied.
- Hardware-specific optimizations make results difficult to generalize across GPU/TPU families.

## Cross-References

- [OpenAI](../entities/openai.md) — GPT models as deployment targets; Sparse Transformer [STATED]
- [Google DeepMind](../entities/google-deepmind.md) — TPU optimization, Chinchilla implications for inference [STATED]
- [Ashish Vaswani](../entities/vaswani-ashish.md) — transformer architecture referenced throughout [STATED]
- [Jared Kaplan](../entities/kaplan-jared.md) — scaling laws inform model sizing decisions [STATED]

## See Also

- [Scaling Laws](../concepts/scaling-laws.md) [STATED]
- [Attention Mechanisms](../concepts/attention-mechanisms.md) [STATED]
- [Compute-Optimal Training](../concepts/compute-optimal-training.md) [STATED]
