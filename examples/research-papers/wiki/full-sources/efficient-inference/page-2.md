## Knowledge Distillation

### Principles

Knowledge distillation transfers knowledge from a large "teacher" to a smaller "student" by training the student to match the teacher's output distribution. The teacher's soft probabilities encode "dark knowledge" about problem structure beyond hard labels.

### Distillation for LLMs

- **Output-level:** Match token-level probability distributions
- **Feature-level:** Align intermediate representations
- **Data-augmented:** Teacher generates synthetic training data for the student (e.g., Alpaca, Vicuna fine-tuned on GPT-4 outputs)

### Scaling Law Implications

The scaling laws suggest smaller models can match larger ones with more training data. Distillation creates a "data multiplier" — the teacher generates unlimited high-quality data, pushing the student toward its compute-optimal frontier per Hoffmann et al.'s Chinchilla analysis.

## KV-Cache Optimization

### The KV-Cache Problem

During autoregressive generation, attention requires key and value projections of all previous tokens. For LLaMA-70B with 80 layers and 64 heads, the KV-cache for a 4,096-token sequence requires ~5GB in FP16.

### Multi-Query and Grouped-Query Attention

MQA shares a single KV head across all query heads (64x reduction). GQA groups heads and shares KV within groups — LLaMA 2 (70B) uses 8 KV groups for 64 query heads (8x reduction).

### PagedAttention and vLLM

Applies virtual memory concepts to KV-cache: fixed-size pages dynamically allocated and shared between sequences. Reduces memory waste from fragmentation and enables efficient batching.

### KV-Cache Compression

- Token dropping based on attention scores
- Quantized KV-cache (INT8/INT4)
- Sliding window attention (Mistral)

## Speculative Decoding

### Core Idea

Uses a small draft model to generate K candidate tokens, verified by the large model in a single forward pass. Preserves the target model's output distribution exactly through modified rejection sampling.

### How It Works

1. Draft model generates K candidates (fast)
2. Target model verifies all K in parallel (single forward pass)
3. Accept/reject via rejection sampling
4. Expected speedup: 2-3x with 70-90% acceptance rates

### Variants

**Self-speculative decoding** uses early layers of the target model as the draft. **Medusa** adds lightweight prediction heads for parallel candidate generation with tree-structured attention verification.
