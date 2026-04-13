# Neural Scaling Laws: A Comprehensive Survey

## Abstract

The study of neural scaling laws has emerged as one of the most consequential areas of machine learning research in recent years. This survey examines the empirical and theoretical foundations of scaling behavior in neural language models, with particular focus on the seminal contributions of Kaplan et al. (2020) from OpenAI and Hoffmann et al. (2022) from Google DeepMind. We trace the development of scaling law research from early observations of power-law relationships to the modern understanding of compute-optimal training, and discuss the profound implications these findings have had on the design and training of large language models. Our analysis reveals that while the fundamental power-law relationships are robust, the optimal allocation of compute budget between model size and dataset size remains an active area of investigation with significant practical consequences.

## Introduction

The rapid progress in natural language processing over the past decade has been driven largely by increases in model scale. From the early word2vec models with millions of parameters to modern large language models (LLMs) with hundreds of billions of parameters, the field has consistently demonstrated that larger models trained on more data tend to perform better across a wide range of tasks. However, it was not until the systematic investigation of scaling behavior that researchers began to understand the precise mathematical relationships governing this phenomenon.

The question of how model performance scales with increased resources — parameters, data, and compute — is not merely academic. Understanding these relationships has direct implications for how organizations allocate computational budgets worth millions of dollars. Should resources be directed toward training a larger model on the same data, or a smaller model on more data? The answer, as we shall see, has shifted significantly as our understanding has deepened.

This survey is organized as follows. We first review the foundational work on neural scaling laws by Jared Kaplan and colleagues at OpenAI. We then examine the compute-optimal training paradigm introduced by Jordan Hoffmann and colleagues at Google DeepMind through the Chinchilla study. We discuss the implications of these findings for the broader machine learning community, and conclude with open questions and directions for future research.
