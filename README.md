


# Physiology Study Assistant

This project is a small language-model study assistant. It uses notes and training text to answer questions, connect related terms, and create practice quizzes.

## Instructions for Build and Use

Steps to build and/or run the software:

1. Install Python 3.10 or newer.
2. Open PowerShell in the project folder.
3. Run `py mini_llm.py` or `study.cmd path\to\notes.txt`.

Instructions for using the software:

1. Run the study mode with a `.txt` or `.md` notes file.
2. Ask questions about terms from the notes or request a quiz.
3. Type `quit` to close the program.
4. Run `py -m unittest discover -s tests -v` to run the tests.

## Development Environment

To recreate the development environment, you need the following software and/or libraries with the specified versions:

* Python 3.10 or newer
* PowerShell or another terminal
* Git and GitHub
* The project mainly uses Python's standard library, so extra packages are not required.

## Useful Websites to Learn More

I found these websites useful in developing this software:

* [Python Documentation](https://docs.python.org/3/)
* [Andrej Karpathy's Neural Network Series](https://karpathy.ai/zero-to-hero.html)
* [LanguageTool Documentation](https://dev.languagetool.org/http-server)
* [Project Gutenberg](https://www.gutenberg.org/)

## Future Work

The following items I plan to fix, improve, and/or add to this project in the future:

* [ ] Improve the autocorrect and related-term matching.
* [ ] Add a larger neural network trained with backpropagation.
* [ ] Improve the ranking of relevant sentences from the notes.
* [ ] Add more physiology study cards and accuracy tests.
* [ ] Create a simple web or desktop chat interface.
* [ ] Add support for more note formats later.









## Below this point was the previous README






This is a compact, document-grounded study assistant. Given `.txt`, `.md`, `.doc`, or `.docx` study notes, it opens a conversational session where you can request study topics, ask factual questions, or take a practice quiz one question at a time. It also retains a small word-to-word language-model demonstration for learning purposes.

It is intentionally small enough to understand in one sitting. It is **not** a modern large language model. Its study mode combines structured fact cards, a small neural term-embedding layer, and grounded sentence retrieval:



```text
study cards + notes -> related-term ranking -> grounded answer or quiz
```

## Create a practice test

Run the study mode with a notes file:

```powershell
py mini_llm.py --study path\to\notes.md
```

Then chat with it:

```text
You: Give me a quiz
Question 1: ...
Your answer: ...
Assistant: Correct. Nice work.
```

This provides the chat-shaped interface locally while keeping the project dependency-free. The structured cards are used first for factual questions; the neural term layer connects related wording; and the note corpus supplies additional context. This retrieval-first design is more reliable for physiology than asking a small neural generator to invent an answer.

The main study data files are:

- `data/processed/physiology_training.txt` — the broader physiology corpus used for retrieval and term relationships.
- `data/processed/physiology_cards.json` — precise question-and-answer facts with topics and textbook section references.
- `docs/FUNCTION_GUIDE.md` — a function-by-function explanation of the code and reusable Python syntax.

## Project layout

```text
llm_prototype/
├── mini_llm.py                 # compatibility launcher
├── src/mini_llm/app.py         # current CLI and orchestration
├── src/mini_llm/models/        # term network and future neural models
├── src/mini_llm/study/         # future parsing, retrieval, quiz modules
├── data/raw/                   # original notes and permitted source material
├── data/processed/             # cleaned training text and reviewed cards
├── tests/                      # collaborator regression tests
└── docs/                       # presentation, function guide, and architecture
```

The current term network in `src/mini_llm/models/term_network.py` is a small
trainable association layer. It learns
vectors from terms that occur in the same sentences, then uses cosine
similarity to expand a user's topic. The next neural-network milestone is to
move that class into `src/mini_llm/models/`, add explicit train/validation
splits, and replace the hand-written update loop with a small multilayer
network trained by backpropagation. The study assistant should continue to
retrieve facts from the notes instead of asking a small model to invent them.

You can also ask `What should I learn?` for an ordered learning plan, ask about a specific term such as `What does DHP do?`, type `skip` to reveal an answer, or type `quit` to end the session. The learning plan connects mechanisms instead of only listing keywords.

In the original demo mode, the prompt is used only as context. The generated continuation is returned without copying the prompt back into the response.

The original question-count option remains available for future quiz-generation improvements:

```powershell
py mini_llm.py --study path\to\notes.txt --questions 12
```

The assistant stays grounded in the supplied notes. It extracts definition-like sentences, key terms, and fill-in-the-blank prompts; it does not know facts that are not in the document. Legacy `.doc` files require Microsoft Word on Windows for text extraction.

Study prompts pass through a conservative vocabulary-aware autocorrect layer
before cross-referencing. It recognizes common physiology misspellings such
as `homeostatis`, `dihydropyradine`, `mitocondria`, and `achesterase` without
rewriting the original notes or aggressively changing ordinary words.

## Run the original demo

Open PowerShell in this folder and type:

```powershell
.\run
```

Or run `py mini_llm.py`. Add reviewed sentences to `data/processed/physiology_training.txt`, run the program again, and observe how the generated text changes.

The project also includes two public-domain historical physiology texts in
`data/raw`. To include them in the word-pattern demo, run:

```powershell
py mini_llm.py --include-open-data
```

They are useful for learning textbook-like sentence patterns, but they are
not treated as current medical truth. The source and licensing details are in
[`data/raw/SOURCES.md`](data/raw/SOURCES.md). The study assistant continues to
prioritize the user's notes and reviewed cards.

## Response accuracy tests

Run the complete test suite with:

```powershell
py -m unittest discover -s tests -v
```

[`tests/test_response_accuracy.py`](tests/test_response_accuracy.py) uses
golden prompts to verify that responses contain evidence from the training
corpus, that reviewed cards return required terms, and that unsupported topics
are not answered with invented facts. Add a new case whenever an important
term or textbook fact is added to the training data.

## What to explain

1. **Tokenization:** text is split into words and punctuation.
2. **Training:** the program counts what token follows each current token.
3. **Inference:** it uses those counts as probabilities for the next token.
4. **Generation:** it repeats prediction until it reaches an end token or a length limit.
5. **Limitation:** this model memorizes local patterns; it does not reason or understand meaning.

## Learn more and choose a next project

See [docs/LEARNING_AND_IDEAS.md](docs/LEARNING_AND_IDEAS.md) for a staged learning path, recommended resources, and potential projects to build next.
