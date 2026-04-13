## Model Pruning and Sparsity

### Structured vs. Unstructured Pruning

**Unstructured pruning** removes individual weights, creating sparse matrices. High compression (90%+) but irregular memory patterns are hard to accelerate on GPUs.

**Structured pruning** removes entire neurons, heads, or layers, maintaining dense operations. More constrained but hardware-friendly.

### SparseGPT

SparseGPT (Frantar & Alistarh, 2023) achieves 50-60% unstructured sparsity in one shot without retraining, using approximate second-order information.

### Mixture of Experts

MoE activates only a subset of parameters per token. Mixtral: 46.7B total parameters, 12.9B active per token through 8-expert MoE layers. Provides large-model capacity at small-model inference cost, though total memory requirements reflect total parameters.

## Hardware Considerations

### GPU Memory Hierarchy

Optimization must account for registers, L1/L2 cache, SRAM, and HBM. Flash Attention demonstrated that careful data movement management yields dramatic speedups without reducing computation.

### TPUs and Custom Hardware

Google's TPUs are optimized for transformer inference with high memory bandwidth and hardware support for matrix multiply, softmax, and top-k operations.

### The Memory Bandwidth Bottleneck

For autoregressive inference, memory bandwidth — not compute — is the bottleneck. Generating one token requires reading all weights but performs little computation per weight. Techniques reducing memory footprint (quantization, pruning) directly improve throughput.

## Interaction with Scaling Laws

A larger model aggressively quantized often outperforms a smaller model at full precision — consistent with scaling law predictions about model capacity. Organizations may benefit from training Chinchilla-optimal models and applying post-training quantization, achieving better quality-per-inference-FLOP than training smaller models natively.

## Conclusion

Efficient inference techniques — quantization, distillation, KV-cache optimization, speculative decoding, and pruning — address different aspects of the deployment challenge and are often complementary. The interplay between these techniques and fundamental scaling laws is increasingly recognized as crucial for optimal deployment decisions.

## References

- Vaswani, A., et al. (2017). Attention is all you need.
- Kaplan, J., et al. (2020). Scaling laws for neural language models.
- Hoffmann, J., et al. (2022). Training compute-optimal large language models.
- Frantar, E., et al. (2022). GPTQ.
- Lin, J., et al. (2023). AWQ.
- Dao, T., et al. (2022). FlashAttention.
- Frantar, E., & Alistarh, D. (2023). SparseGPT.
- Kwon, W., et al. (2023). PagedAttention.
