# Prototype architecture

```text
notes (.txt/.md/.doc/.docx)
        |
        v
  text extraction and sentence splitting
        |
        +--> structured cards ------+
        |                            |
        +--> term network -----------+--> grounded study answer / quiz chat
        |
        +--> sentence corpus ------->+

processed training text --> word-level next-token demo
```

## Responsibilities

- `data/raw/`: original notes and textbook excerpts that are allowed to be
  used.
- `data/processed/`: cleaned text and manually reviewed fact cards.
- `src/mini_llm/app.py`: current dependency-free CLI and orchestration.
- `src/mini_llm/models/`: home for trainable neural components.
- `src/mini_llm/study/`: future document parsing, retrieval, quiz, and scoring
  modules.
- `tests/`: small regression tests that collaborators can extend.

The current system is a retrieval-first educational prototype, not a modern
large language model. The term network learns associations between terms, but
it does not replace a language model or guarantee factual correctness.
