## Multi-Head Self-Attention

### The Multi-Head Mechanism

Vaswani et al. observed that rather than performing a single attention function with d_model-dimensional keys, values, and queries, it is beneficial to linearly project the queries, keys, and values h times with different, learned linear projections. On each of these projected versions, attention is performed in parallel, yielding outputs that are concatenated and projected:

MultiHead(Q, K, V) = Concat(head_1, ..., head_h) W^O
where head_i = Attention(Q W_i^Q, K W_i^K, V W_i^V)

### Why Multiple Heads Matter

Multiple attention heads allow the model to jointly attend to information from different representation subspaces at different positions. In practice, different heads learn to attend to different types of relationships: syntactic (subject-verb agreement), semantic (coreference), and positional (previous/next token).

## Positional Encoding

### The Position Problem

Because the transformer contains no recurrence and no convolution, it has no inherent notion of token order. To enable the model to use sequence order, Vaswani et al. introduced positional encodings added to input embeddings.

### Sinusoidal Encoding

The original transformer used fixed sinusoidal positional encodings:
PE(pos, 2i) = sin(pos / 10000^(2i/d_model))
PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))

### Modern Alternatives

Rotary Positional Encoding (RoPE) has become dominant in modern LLMs including LLaMA. ALiBi adds linearly increasing penalties based on distance.

## The Transformer Architecture

### Encoder-Decoder Structure

The original transformer follows an encoder-decoder architecture with stacks of identical layers containing self-attention and feed-forward sub-layers with residual connections and layer normalization.

### Decoder-Only Models

The most successful language models have adopted decoder-only architectures. GPT from OpenAI demonstrated that a decoder-only transformer with causal attention masking could achieve strong performance through pre-training followed by fine-tuning. Models like GPT-3, GPT-4, PaLM, and LLaMA all use decoder-only transformers.
