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
