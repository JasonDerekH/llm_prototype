# Learning Path and Project Ideas

This file keeps longer-term study notes separate from the quick-start instructions in [README.md](README.md).

## Suggested learning path

1. Learn Python, probability, vectors, and matrix multiplication.
2. Study neural networks and gradient descent.
3. Build a classifier with PyTorch before building a language model.
4. Learn tokenization, embeddings, positional information, self-attention, and Transformers.
5. Build a tiny Transformer on a small dataset and track training and validation loss.
6. Learn evaluation, data cleaning, bias, privacy, prompt injection, and deployment costs.
7. For a practical application, start with a pretrained open-source model and fine-tune it or use retrieval-augmented generation instead of training a foundation model from scratch.

## Recommended resources

- [Attention Is All You Need](https://arxiv.org/abs/1706.03762) — the original Transformer paper.
- [The Illustrated Transformer](https://jalammar.github.io/illustrated-transformer/) — a visual explanation of attention and Transformer components.
- [PyTorch tutorials](https://pytorch.org/tutorials/) — practical neural-network and deep-learning exercises.
- [Hugging Face course](https://huggingface.co/learn/nlp-course/chapter1/1) — tokenizers, Transformers, datasets, and model workflows.
- [Andrej Karpathy's Zero to Hero](https://karpathy.ai/zero-to-hero.html) — neural networks and language models built from scratch.

## Potential projects to build

Start with a project whose dataset and success criteria are small enough to evaluate. Possible directions include:

1. **Story or poem generator** — train on a small, public-domain collection and compare different sampling temperatures.
2. **Course-notes assistant** — answer questions using a small set of class notes, with citations to the source passages.
3. **Command-line coding tutor** — explain short code snippets, generate exercises, and check answers using a constrained dataset.
4. **Recipe assistant** — generate recipes from available ingredients while following dietary and allergy constraints.
5. **Game dialogue generator** — produce dialogue for a small set of characters while maintaining each character's style.
6. **Text classifier plus explanation** — classify support messages, news topics, or product reviews and show which words influenced the result.
7. **Retrieval-augmented FAQ bot** — retrieve relevant documents first, then generate an answer grounded in those documents.
8. **Tiny Transformer reproduction** — replace this counting model with a small Transformer and chart training loss and validation loss.
9. **Multilingual next-token model** — compare tokenization and prediction quality across two languages using a small parallel dataset.
10. **Model evaluation dashboard** — run a fixed prompt set and track accuracy, repetition, response length, latency, and failure cases over time.

For a first extension of this prototype, the most direct choice is the tiny Transformer reproduction: keep the current tokenization and generation interface, replace the next-token counts with learned embeddings and attention, and add a held-out validation set.
