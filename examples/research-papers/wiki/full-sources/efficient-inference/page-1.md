# Efficient Inference for Large Language Models

## Abstract

As large language models have grown from millions to hundreds of billions of parameters, the challenge of serving these models efficiently at inference time has become a critical bottleneck for deployment. This paper surveys the major approaches to efficient LLM inference, including quantization, knowledge distillation, KV-cache optimization, speculative decoding, and model pruning.

## Introduction

The remarkable capabilities demonstrated by large language models have created unprecedented demand for efficient inference. While training a frontier LLM is a one-time cost, inference costs scale with every user query and every API call. For organizations serving millions of users, inference costs can exceed training costs within months.

The fundamental challenge is rooted in the transformer architecture of Vaswani et al. (2017). These models are dense, with every parameter participating in every forward pass, and autoregressive generation requires sequential token-by-token computation. Understanding the scaling laws of Kaplan et al. (2020) and Hoffmann et al. (2022) provides crucial context: larger models are more sample-efficient during training but imply proportionally larger inference costs.

## Quantization

### Overview

Quantization reduces numerical precision of model weights and/or activations from FP16/BF16 to lower bit-widths (INT8, INT4, or binary). Since memory bandwidth is typically the inference bottleneck, reducing bytes per parameter directly improves throughput.

### Post-Training Quantization

**GPTQ** (Frantar et al., 2022) uses approximate second-order information (the Hessian) to determine optimal quantized values, processing weights column by column. Achieves 3-4 bit quantization with minimal quality loss.

**AWQ** (Lin et al., 2023) identifies "salient" weights that process the most important activation channels, protecting them while quantizing the rest more aggressively.

### Quantization-Aware Training

QAT incorporates quantization into the training loop, allowing weights to adapt to lower precision. Generally produces higher-quality results than PTQ but requires training infrastructure access.

### Mixed-Precision Inference

Modern frameworks keep sensitive layers at higher precision while quantizing the bulk of the model. Combined with GPU/TPU mixed-precision hardware support, this achieves most throughput benefits with minimal quality impact.
