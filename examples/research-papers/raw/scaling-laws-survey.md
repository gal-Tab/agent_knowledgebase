# Neural Scaling Laws: A Comprehensive Survey

## Abstract

The study of neural scaling laws has emerged as one of the most consequential areas of machine learning research in recent years. This survey examines the empirical and theoretical foundations of scaling behavior in neural language models, with particular focus on the seminal contributions of Kaplan et al. (2020) from OpenAI and Hoffmann et al. (2022) from Google DeepMind. We trace the development of scaling law research from early observations of power-law relationships to the modern understanding of compute-optimal training, and discuss the profound implications these findings have had on the design and training of large language models. Our analysis reveals that while the fundamental power-law relationships are robust, the optimal allocation of compute budget between model size and dataset size remains an active area of investigation with significant practical consequences.

## Introduction

The rapid progress in natural language processing over the past decade has been driven largely by increases in model scale. From the early word2vec models with millions of parameters to modern large language models (LLMs) with hundreds of billions of parameters, the field has consistently demonstrated that larger models trained on more data tend to perform better across a wide range of tasks. However, it was not until the systematic investigation of scaling behavior that researchers began to understand the precise mathematical relationships governing this phenomenon.

The question of how model performance scales with increased resources — parameters, data, and compute — is not merely academic. Understanding these relationships has direct implications for how organizations allocate computational budgets worth millions of dollars. Should resources be directed toward training a larger model on the same data, or a smaller model on more data? The answer, as we shall see, has shifted significantly as our understanding has deepened.

This survey is organized as follows. We first review the foundational work on neural scaling laws by Jared Kaplan and colleagues at OpenAI. We then examine the compute-optimal training paradigm introduced by Jordan Hoffmann and colleagues at Google DeepMind through the Chinchilla study. We discuss the implications of these findings for the broader machine learning community, and conclude with open questions and directions for future research.

## Foundational Scaling Laws: Kaplan et al. (2020)

### The OpenAI Scaling Laws Paper

In January 2020, Jared Kaplan, Sam McCandlish, Tom Henighan, and colleagues at OpenAI published "Scaling Laws for Neural Language Models," a landmark paper that systematically characterized how the cross-entropy loss of autoregressive language models depends on model size, dataset size, and the amount of compute used for training. This work, conducted as part of OpenAI's broader research program into large language models, established the empirical framework that would guide subsequent scaling decisions across the industry.

### Power-Law Relationships

The central finding of Kaplan et al. was that test loss follows smooth power-law relationships as a function of each scaling factor, when the other factors are not bottlenecked. Specifically, they observed:

**Loss vs. Parameters (N):** L(N) ∝ N^(-0.076), meaning that for every 10x increase in model parameters, test loss decreases by approximately 0.076 on a log scale.

**Loss vs. Dataset Size (D):** L(D) ∝ D^(-0.095), indicating that performance also improves predictably with dataset size, though with a slightly different exponent.

**Loss vs. Compute (C):** L(C) ∝ C^(-0.050), showing that performance improvement per unit compute follows its own power law.

These relationships were observed to hold over many orders of magnitude, spanning models from 768 parameters to 1.5 billion parameters, and datasets from 22 million to 23 billion tokens.

### Key Insights from Kaplan et al.

Several important insights emerged from this work:

1. **Smooth and predictable scaling.** Performance improvements are remarkably predictable across many orders of magnitude, allowing researchers to extrapolate expected performance of larger models from smaller experiments.

2. **Model size dominance.** Kaplan et al. concluded that model size is more important than dataset size for a fixed compute budget. Their analysis suggested that as compute budget increases, model size should be scaled more aggressively than dataset size, following an approximately N ∝ C^(0.73) relationship.

3. **Convergence is not necessary.** They observed that larger models reach any given level of performance with fewer optimization steps than smaller models, and with less total data processed. This suggested an approach of training very large models for relatively few steps.

4. **Architecture independence.** The scaling laws appeared relatively insensitive to architectural details such as depth vs. width, attention head count, and other hyperparameters, suggesting these relationships reflect something fundamental about the learning problem rather than specific architectural choices.

## Compute-Optimal Training: The Chinchilla Paradigm

### Challenging the Kaplan Assumptions

In March 2022, Jordan Hoffmann, Sebastian Borgeaud, Arthur Mensch, and colleagues at Google DeepMind published "Training Compute-Optimal Large Language Models," commonly referred to as the Chinchilla paper. This work fundamentally challenged one of the key conclusions of Kaplan et al. — namely, the optimal ratio of model parameters to training tokens.

### The Chinchilla Methodology

Hoffmann et al. took a more rigorous approach to determining the optimal allocation of a fixed compute budget between model size and training data. They conducted over 400 training runs with models ranging from 70 million to 16 billion parameters, trained on 5 billion to 500 billion tokens from the MassiveText dataset assembled by Google DeepMind.

Their analysis employed three complementary approaches:

1. **Fixed compute, varying model/data ratios:** For several fixed compute budgets, they trained models of different sizes and determined which achieved the lowest loss.

2. **IsoFLOP profiles:** They analyzed the loss landscape at fixed computational costs to identify optimal model sizes.

3. **Parametric fitting:** They fit a parametric loss function to their experimental data to derive optimal scaling coefficients.

### The Chinchilla Result

All three approaches converged on a consistent result: model parameters and training tokens should scale approximately equally with compute budget. Specifically, for a given compute budget C, the optimal model size N and training dataset size D should satisfy:

- N_opt ∝ C^(0.50) (compared to Kaplan's N ∝ C^(0.73))
- D_opt ∝ C^(0.50) (compared to Kaplan's implicit D ∝ C^(0.27))

This means that the optimal number of training tokens is approximately 20 times the number of model parameters — a dramatically different prescription from Kaplan et al.'s recommendation, which would have called for far fewer tokens relative to parameters.

### Chinchilla vs. Gopher

To demonstrate the practical significance of their findings, Hoffmann et al. trained Chinchilla, a 70-billion parameter model, on 1.4 trillion tokens. Despite having four times fewer parameters than Google DeepMind's own Gopher model (280B parameters, trained on 300B tokens), Chinchilla outperformed Gopher on the majority of evaluated benchmarks. This powerfully illustrated that many existing large language models were significantly undertrained relative to the compute-optimal frontier.

## Implications for Large Language Model Training

### The Training Paradigm Shift

The Chinchilla findings precipitated a paradigm shift in how organizations approach LLM training. Prior to Chinchilla, the prevailing wisdom — informed by Kaplan et al.'s analysis — was to make models as large as possible within a compute budget and train them for relatively few steps. After Chinchilla, the field moved toward training more appropriately-sized models on significantly more data.

This shift is visible in subsequent model releases. Meta AI's LLaMA models, for instance, explicitly followed compute-optimal training principles, with the 7B parameter variant trained on 1 trillion tokens (approximately a 140:1 token-to-parameter ratio), and the 65B parameter variant also trained on 1.4 trillion tokens.

### Economic Implications

The scaling laws have profound economic implications. Training a frontier language model requires tens of millions of dollars in compute costs. The difference between Kaplan-optimal and Chinchilla-optimal allocation of that budget can mean the difference between a model that leads benchmarks and one that underperforms models a fraction of its size. For organizations like OpenAI and Google DeepMind competing at the frontier, understanding and correctly applying scaling laws represents a significant competitive advantage.

### Scaling Beyond Chinchilla

Recent research has begun to explore whether the Chinchilla scaling laws continue to hold at even larger scales. Some evidence suggests that at very large compute budgets, the optimal training may involve even more data relative to parameters than Chinchilla predicted. Additionally, techniques like repeated data, synthetic data generation, and data quality filtering complicate the simple data-scaling picture.

## Attention Mechanisms and Scaling

An important question is how the fundamental architecture of transformer models — particularly the attention mechanism introduced by Vaswani et al. (2017) — interacts with scaling behavior. The self-attention operation has O(n²) complexity in sequence length, which creates practical constraints on scaling. Recent work on efficient attention variants, including Flash Attention and various linear attention approximations, aims to relax these constraints and enable more efficient scaling of both model size and context length.

The interaction between scaling laws and architectural innovations in attention remains an active research area. Some evidence suggests that the power-law scaling exponents may differ for models using different attention mechanisms, though the fundamental relationships remain qualitatively similar.

## Open Questions and Future Directions

Several important questions remain open in scaling law research:

1. **Transfer and downstream task scaling.** The original scaling laws characterize pre-training loss. How performance on specific downstream tasks scales with model size is less well understood and potentially more relevant for practical applications.

2. **Multimodal scaling.** As models increasingly handle multiple modalities (text, images, audio, video), the scaling relationships may become more complex. Early work from both OpenAI and Google DeepMind suggests that multimodal scaling laws exist but with different characteristics.

3. **Data quality vs. quantity.** The scaling laws typically assume a fixed data distribution. How data curation, filtering, and synthesis interact with scaling remains poorly understood.

4. **Inference-time scaling.** Recent work on chain-of-thought reasoning and test-time compute suggests that there may be complementary scaling laws governing how performance improves with additional computation at inference time, separate from pre-training compute.

5. **Diminishing returns.** Whether the power-law relationships eventually break down — hitting a wall where additional scale produces negligible improvements — remains an open and consequential question.

## Conclusion

Neural scaling laws have transformed our understanding of how to train large language models efficiently. The progression from Kaplan et al.'s initial characterization of power-law relationships to Hoffmann et al.'s compute-optimal training prescription represents a rapid maturation of our empirical understanding. These insights have directly influenced the training strategies of every major AI laboratory, from OpenAI to Google DeepMind to Meta AI, and have reshaped the economics of AI development.

As the field continues to push toward ever-larger scales of computation, the importance of understanding scaling behavior will only grow. The researchers who first characterized these relationships — Jared Kaplan, Jordan Hoffmann, and their collaborators — have provided the community with tools that save billions of dollars in wasted compute and accelerate the development of more capable AI systems.

## References

- Kaplan, J., McCandlish, S., Henighan, T., Brown, T. B., Chess, B., Child, R., ... & Amodei, D. (2020). Scaling laws for neural language models. arXiv:2001.08361.
- Hoffmann, J., Borgeaud, S., Mensch, A., Buchatskaya, E., Cai, T., Rutherford, E., ... & Sifre, L. (2022). Training compute-optimal large language models. arXiv:2203.15556.
- Brown, T. B., Mann, B., Ryder, N., Subbiah, M., et al. (2020). Language models are few-shot learners. NeurIPS 2020.
- Touvron, H., Lavril, T., Izacard, G., et al. (2023). LLaMA: Open and efficient foundation language models. arXiv:2302.13971.
- Vaswani, A., Shazeer, N., Parmar, N., et al. (2017). Attention is all you need. NeurIPS 2017.
- Rae, J. W., Borgeaud, S., Cai, T., et al. (2021). Scaling language models: Methods, analysis & insights from training Gopher. arXiv:2112.11446.
