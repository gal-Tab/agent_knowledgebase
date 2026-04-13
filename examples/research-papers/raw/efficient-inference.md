# Efficient Inference for Large Language Models: Techniques, Trade-offs, and Future Directions

## Abstract

As large language models (LLMs) have grown from millions to hundreds of billions of parameters, the challenge of serving these models efficiently at inference time has become a critical bottleneck for deployment. This paper surveys the major approaches to efficient LLM inference, including quantization, knowledge distillation, KV-cache optimization, speculative decoding, and model pruning. We examine how each technique interacts with the transformer architecture — particularly the attention mechanism introduced by Vaswani et al. (2017) — and discuss the implications of neural scaling laws for inference optimization. Our analysis draws on work from leading research organizations including OpenAI, Google DeepMind, Meta AI, and the broader open-source community, and highlights the hardware considerations that increasingly drive algorithmic choices in this space.

## Introduction

The remarkable capabilities demonstrated by large language models have created unprecedented demand for efficient inference. While training a frontier LLM is a one-time cost (albeit a massive one), inference costs scale with every user query, every API call, and every deployed application. For organizations serving millions of users, inference costs can exceed training costs within months of deployment.

The fundamental challenge is rooted in the architecture itself. The transformer models that power modern LLMs, based on the attention mechanism architecture of Vaswani et al. (2017), were designed to maximize learning capacity during training. The resulting models are dense, with every parameter participating in every forward pass, and the autoregressive generation process requires sequential token-by-token computation that is inherently difficult to parallelize.

Understanding the relationship between model size and performance — as characterized by the scaling laws of Kaplan et al. (2020) at OpenAI and the compute-optimal training principles of Hoffmann et al. (2022) at Google DeepMind — provides crucial context for inference optimization. These scaling laws tell us that larger models are more sample-efficient during training, but they also imply that the performance gains from scale come with proportionally larger inference costs. The goal of efficient inference research is to break this proportionality: achieving the performance of a large model at a fraction of the computational cost.

## Quantization

### Overview

Quantization reduces the numerical precision of model weights and/or activations from the standard 16-bit floating point (FP16 or BF16) to lower bit-widths such as INT8, INT4, or even binary representations. Since memory bandwidth is typically the bottleneck for autoregressive LLM inference, reducing the number of bytes per parameter directly improves throughput.

### Post-Training Quantization (PTQ)

The simplest approach is to quantize a pre-trained model without any additional training. Naive round-to-nearest quantization to INT8 typically preserves most of the model's quality, but more aggressive quantization to INT4 or below can cause significant degradation without careful handling.

**GPTQ** (Frantar et al., 2022) addresses this by using approximate second-order information (the Hessian) to determine the optimal quantized values for each weight, processing weights column by column. GPTQ can quantize models to 3-4 bits with minimal quality loss and has become one of the most widely used quantization methods in the open-source community.

**AWQ** (Activation-Aware Weight Quantization, Lin et al., 2023) takes a different approach, observing that not all weights are equally important. By identifying the small fraction of "salient" weights — those that process the most important activation channels — AWQ protects these critical weights while quantizing the rest more aggressively. This insight allows AWQ to achieve better quality than GPTQ at the same bit-width in many scenarios.

### Quantization-Aware Training (QAT)

Quantization-aware training incorporates the quantization operation into the training loop itself, allowing the model to adapt its weights to the lower precision representation. While QAT generally produces higher-quality quantized models than PTQ, it requires access to training infrastructure and significant computational resources, making it impractical for many practitioners who are fine-tuning or deploying existing models.

### Mixed-Precision Inference

Modern inference frameworks often employ mixed-precision strategies, keeping certain sensitive layers (such as the first and last layers, or attention projections) at higher precision while quantizing the bulk of the model. This approach, combined with hardware support for mixed-precision computation on modern GPUs and TPUs, can achieve most of the throughput benefits of full quantization with minimal quality impact.

## Knowledge Distillation

### Principles

Knowledge distillation transfers knowledge from a large "teacher" model to a smaller "student" model by training the student to match the teacher's output distribution rather than (or in addition to) the hard labels of the training data. The insight, originally from Hinton et al. (2015), is that the teacher's soft probability distribution over the vocabulary contains more information than the hard labels alone — the relative probabilities assigned to incorrect tokens encode the teacher's "dark knowledge" about the structure of the problem.

### Distillation for LLMs

In the context of large language models, distillation has been applied at multiple levels:

**Output-level distillation** trains the student to match the teacher's token-level probability distributions. This is the most straightforward approach but requires running the teacher model for every training example.

**Feature-level distillation** additionally aligns intermediate representations between teacher and student, providing richer supervisory signals. This requires architectural compatibility between the two models.

**Data-augmented distillation** uses the teacher to generate synthetic training data, which the student then trains on directly. This approach has been particularly successful — the Alpaca and Vicuna models demonstrated that relatively small models fine-tuned on GPT-4-generated data can achieve impressive capabilities.

### Scaling Law Implications

The scaling laws described by Kaplan et al. suggest that smaller models can achieve performance levels comparable to larger models if given sufficiently more training data. Distillation can be viewed as a way to create a "data multiplier" — the teacher effectively generates infinite high-quality training data for the student, potentially pushing the student toward its compute-optimal frontier as described by Hoffmann et al.'s Chinchilla analysis.

## KV-Cache Optimization

### The KV-Cache Problem

During autoregressive generation with transformer models, the attention mechanism requires access to the key and value projections of all previously generated tokens. These are stored in the KV-cache, which grows linearly with sequence length and can consume substantial GPU memory. For a model like LLaMA-70B with 80 layers and 64 attention heads, the KV-cache for a single 4,096-token sequence requires approximately 5GB of memory in FP16.

### Multi-Query and Grouped-Query Attention

Multi-Query Attention (MQA), proposed by Shazeer (2019), reduces KV-cache size by sharing a single set of key and value heads across all attention heads while maintaining separate query heads. This reduces KV-cache memory by a factor equal to the number of attention heads (e.g., 64x for a 64-head model).

Grouped-Query Attention (GQA) represents a compromise, grouping attention heads and sharing KV projections within each group. LLaMA 2 (70B) uses GQA with 8 KV groups for 64 query heads, reducing KV-cache by 8x while preserving most of the quality of full multi-head attention.

### PagedAttention and vLLM

PagedAttention, implemented in the vLLM framework, applies operating system concepts of virtual memory and paging to KV-cache management. Rather than allocating contiguous memory blocks for each sequence, PagedAttention manages KV-cache in fixed-size pages that can be dynamically allocated and shared between sequences. This dramatically reduces memory waste from internal fragmentation and enables efficient batch processing of sequences with different lengths.

### KV-Cache Compression

Several approaches compress the KV-cache directly:

- **Token dropping** identifies and removes less important tokens from the cache based on attention scores
- **Quantized KV-cache** stores cached keys and values in lower precision (INT8 or INT4)
- **Sliding window attention** limits the cache to only the most recent tokens, as used in Mistral

## Speculative Decoding

### Core Idea

Speculative decoding accelerates autoregressive generation by using a small, fast "draft" model to generate multiple candidate tokens in parallel, which are then verified by the large target model in a single forward pass. Since the large model can process multiple tokens simultaneously (as in prefill), this amortizes the cost of the large model across multiple generated tokens.

### How It Works

1. The draft model generates K candidate tokens autoregressively (fast, small model)
2. The target model processes all K candidates in parallel (single forward pass)
3. The target model's output probabilities are compared against the draft model's choices
4. Tokens are accepted or rejected based on a modified rejection sampling scheme that preserves the target model's output distribution exactly

The expected speedup depends on the acceptance rate — how often the draft model's predictions match the target model's. For a well-chosen draft model, acceptance rates of 70-90% are common for typical text, yielding 2-3x speedups without any change in output quality.

### Variants

**Self-speculative decoding** eliminates the need for a separate draft model by using early layers of the target model itself as the draft, skipping later layers. This reduces the memory overhead of maintaining two models.

**Medusa** (Cai et al., 2024) adds multiple lightweight prediction heads to the target model, each trained to predict future tokens. This enables parallel candidate generation without a separate draft model, and the verification can be done efficiently using tree-structured attention.

## Model Pruning and Sparsity

### Structured vs. Unstructured Pruning

**Unstructured pruning** removes individual weights based on magnitude or other importance criteria, creating sparse weight matrices. While this can achieve high compression ratios (90%+ sparsity), the resulting irregular memory access patterns are difficult to accelerate on standard GPU hardware.

**Structured pruning** removes entire neurons, attention heads, or layers, maintaining dense matrix operations that can be efficiently executed on standard hardware. The trade-off is that structured pruning is more constrained and typically achieves lower compression ratios for the same quality degradation.

### The SparseGPT Approach

SparseGPT (Frantar & Alistarh, 2023) demonstrated that large language models can be pruned to 50-60% unstructured sparsity in a single shot, without any retraining, while maintaining reasonable quality. Like GPTQ, it uses approximate second-order information to determine which weights to prune and how to adjust the remaining weights to compensate.

### Mixture of Experts

While not strictly pruning, Mixture of Experts (MoE) architectures achieve effective sparsity by activating only a subset of the model's parameters for each input token. The Mixtral model, for example, has 46.7 billion total parameters but activates only 12.9 billion per token through its 8-expert MoE layer. This effectively provides the capacity of a much larger model at the inference cost of a smaller one, though total memory requirements remain proportional to total parameters.

## Hardware Considerations

### GPU Architecture and Memory Hierarchy

Efficient inference optimization must account for the GPU memory hierarchy: registers, L1/L2 cache, shared memory (SRAM), and high-bandwidth memory (HBM). The Flash Attention algorithm (Dao et al., 2022) demonstrated that careful management of data movement between these levels can yield dramatic speedups even without reducing total computation. Similar principles apply to inference: many optimization techniques are fundamentally about keeping data closer to compute.

### TPUs and Custom Hardware

Google's Tensor Processing Units (TPUs) and other custom accelerators are increasingly optimized for transformer inference workloads. Google DeepMind and Google Cloud have designed TPU architectures with high memory bandwidth and hardware support for the specific operations (matrix multiply, softmax, top-k) that dominate LLM inference.

### The Memory Bandwidth Bottleneck

For autoregressive LLM inference, the primary bottleneck is memory bandwidth rather than compute. Generating a single token requires reading all model weights from memory but performs relatively little computation per weight. This means that techniques reducing memory footprint (quantization, pruning) directly improve throughput, while techniques reducing computation (efficient attention) may have less impact than expected.

## Interaction with Scaling Laws

The scaling laws established by Kaplan et al. and Hoffmann et al. primarily characterize the relationship between training compute and model quality. For inference, a complementary question arises: given a fixed inference budget (latency, throughput, or cost), what combination of model size and inference optimization technique maximizes quality?

Some researchers have begun to characterize "inference scaling laws" that account for techniques like quantization and distillation. Early results suggest that a larger model, aggressively quantized, often outperforms a smaller model at full precision — consistent with the observation that model capacity (in terms of original parameter count) is a strong predictor of quality even when the effective precision is reduced.

This insight connects directly to the compute-optimal training paradigm: organizations may benefit from training larger-than-needed models following Chinchilla-optimal recipes and then applying aggressive post-training quantization for deployment, achieving better quality-per-inference-FLOP than training smaller models natively.

## Conclusion

Efficient inference for large language models is a rapidly evolving field driven by the practical demands of deploying increasingly capable but resource-intensive models. The techniques surveyed here — quantization, distillation, KV-cache optimization, speculative decoding, and pruning — each address different aspects of the efficiency challenge and are often complementary.

The interplay between these techniques and the fundamental scaling laws that govern model training is increasingly recognized as crucial for making optimal deployment decisions. As Vaswani et al.'s transformer architecture continues to underpin the most capable AI systems, and as the scaling law research of Kaplan, Hoffmann, and others continues to inform how these models are trained, the inference optimization community must continue to develop techniques that unlock the benefits of scale without incurring proportional deployment costs.

## References

- Vaswani, A., Shazeer, N., Parmar, N., et al. (2017). Attention is all you need. NeurIPS 2017.
- Kaplan, J., McCandlish, S., Henighan, T., et al. (2020). Scaling laws for neural language models. arXiv:2001.08361.
- Hoffmann, J., Borgeaud, S., Mensch, A., et al. (2022). Training compute-optimal large language models. arXiv:2203.15556.
- Frantar, E., Ashkboos, S., Hoefler, T., & Alistarh, D. (2022). GPTQ: Accurate post-training quantization for generative pre-trained transformers. arXiv:2210.17323.
- Lin, J., Tang, J., Tang, H., Yang, S., Dang, X., & Han, S. (2023). AWQ: Activation-aware weight quantization for LLM compression and acceleration. arXiv:2306.00978.
- Dao, T., Fu, D. Y., Ermon, S., Rudra, A., & Re, C. (2022). FlashAttention: Fast and memory-efficient exact attention with IO-awareness. NeurIPS 2022.
- Leviathan, Y., Kalman, M., & Matias, Y. (2023). Fast inference from transformers via speculative decoding. ICML 2023.
- Frantar, E., & Alistarh, D. (2023). SparseGPT: Massive language models can be accurately pruned in one-shot. ICML 2023.
- Kwon, W., Li, Z., Zhuang, S., et al. (2023). Efficient memory management for large language model serving with PagedAttention. SOSP 2023.
- Shazeer, N. (2019). Fast transformer decoding: One write-head is all you need. arXiv:1911.02150.
