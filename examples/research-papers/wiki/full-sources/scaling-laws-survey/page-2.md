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
