# Model components

The current working model components are still intentionally compact:

- `TermNetwork` in `src/mini_llm/models/term_network.py` learns small term vectors from words
  appearing in the same sentences. It is the first neural-style layer.
- `MiniLanguageModel` in `src/mini_llm/app.py` is a word-level bigram model
  for demonstrating next-token prediction.

As the project grows, move these classes into separate modules here. A natural
next step is a tiny multilayer perceptron trained with backpropagation, then a
small attention model. Keep retrieval and fact checking separate from text
generation so answers remain grounded in the user's notes.
