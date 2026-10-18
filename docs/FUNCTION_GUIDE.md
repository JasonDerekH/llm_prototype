# Function Guide

This guide explains the reusable functions in `mini_llm.py`. Each section uses bullet points so you can trace the data flow and reuse individual patterns in another Python project.

## Python syntax used throughout

- `name: str` is a type hint: it says the variable or parameter should contain a string.
- `-> list[str]` is a return type hint: the function returns a list of strings. Type hints help readers and code editors, but Python does not require them at runtime.
- `dict[str, object]` means a dictionary with string keys and values that may be different types.
- `list[dict[str, object]] | None` means the value can be a list of dictionaries or `None`. The `|` syntax is a union type.
- `f"{value}"` is an f-string. Expressions inside braces are evaluated and inserted into the string.
- `[expression for item in items if condition]` is a list comprehension. It builds a list in one readable line.
- `with resource:` is a context manager. It automatically closes the resource, even if an error occurs.
- `key=...` in `sorted`, `max`, or `min` tells Python what value to use for comparison.
- A leading underscore, as in `_learn`, conventionally means “internal helper; callers normally do not use this directly.”

## Text and file functions

### `tokenize(text)`

- **Purpose:** Converts text into lowercase words and punctuation tokens for the demo language model.
- **How it works:** `re.findall` searches the entire string and returns every match of the regular expression.
- **Important syntax:** `[A-Za-z']+` matches one or more letters or apostrophes; `[.!?,]` matches one punctuation character.
- **Reusable pattern:** Use this when a project needs a simple tokenizer without a third-party library. It intentionally does not handle every language, number, or special symbol.

### `load_notes(path)`

- **Purpose:** Reads `.txt` and `.md` files and extracts text from `.docx` or legacy `.doc` files.
- **How it works:** `path.suffix.lower()` chooses the reader based on the file extension.
- **Important syntax:** `read_text(encoding="utf-8")` prevents most character-encoding problems for normal text files.
- **DOCX branch:** A DOCX file is a ZIP archive. `ZipFile` opens it, `archive.read("word/document.xml")` reads the document XML, and `ElementTree` collects text nodes whose tag ends in `}t`.
- **DOC branch:** A legacy `.doc` file is binary, so the function calls Microsoft Word through PowerShell COM to extract visible document text.
- **Reusable pattern:** This is a good example of a single interface hiding several file-format implementations. Callers only need to provide a `Path`.

### `load_cards(path)`

- **Purpose:** Loads the structured fact cards from `data/processed/physiology_cards.json`.
- **How it works:** `json.loads` converts file text into Python lists and dictionaries.
- **Validation:** It checks that the top level is a list and keeps only dictionaries containing both `question` and `answer`.
- **Reusable pattern:** Validate external data at the boundary of a program so later functions can assume a cleaner data shape.

### `sentences(text)`

- **Purpose:** Splits notes into normalized sentences that are long enough to be useful for retrieval.
- **How it works:** `re.split` cuts on punctuation followed by whitespace or on line breaks. `re.sub` collapses repeated whitespace.
- **Important syntax:** `(?<=[.!?])` is a positive lookbehind. It checks that the split occurs after sentence punctuation without including that punctuation in the match.
- **Filtering:** `if len(item.split()) >= 3` removes headings or fragments that are too short to provide useful context.
- **Reusable pattern:** Use this as a lightweight document chunker before search, summarization, or question generation.

### `content_words(text)`

- **Purpose:** Extracts lowercase words that are useful for topic matching.
- **How it works:** It finds words with at least three letters and removes words in `STOP_WORDS`.
- **Why it matters:** Removing common words makes matching “What does ADH do?” focus on `adh` instead of words such as `what` and `does`.
- **Reusable pattern:** This is a simple keyword-normalization stage for search or classification.

## `TermNetwork` methods

### `TermNetwork.__init__(dimensions=8, epochs=20)`

- **Purpose:** Creates the small neural term-embedding model.
- **How it works:** It stores the vector length, training-pass count, an empty vector dictionary, and a seeded random generator.
- **Important syntax:** `random.Random(7)` creates a separate deterministic random generator. The fixed seed makes results repeatable between runs.
- **Reusable pattern:** Store model configuration in an object so training and prediction share the same learned state.

### `TermNetwork.fit(source_sentences)`

- **Purpose:** Learns which words are related because they occur in the same sentence.
- **Vocabulary:** The set comprehension collects unique content words across all sentences. `sorted` makes the order deterministic.
- **Training pairs:** `dict.fromkeys(words)` removes duplicates while preserving order. Nested comprehensions create every distinct word pair in a sentence.
- **Neural step:** Each positive pair is trained toward a high dot product. A randomly selected negative pair is trained toward a low dot product.
- **Reusable pattern:** This demonstrates a tiny embedding-training loop. It is educational and useful for local term association, but it is not a replacement for a pretrained language model.

### `TermNetwork._learn(left, right, target)`

- **Purpose:** Performs one gradient-style update on two term vectors.
- **How it works:** It computes a dot-product score, compares it to the target, and adjusts both vectors in the direction that reduces the error.
- **Important syntax:** `zip(first, second)` pairs corresponding vector components so the update can run dimension by dimension.
- **Reusable pattern:** The same structure appears in many simple machine-learning optimizers: prediction, error, learning rate, and parameter update.

### `TermNetwork.related(term, limit=3)`

- **Purpose:** Finds terms whose learned vectors are closest to a requested term.
- **How it works:** It calculates cosine similarity between the requested vector and every other vector.
- **Important syntax:** `or 1` prevents division by zero when a vector has zero length.
- **Sorting:** `sorted(scores, reverse=True)` places the highest similarity first, and `[:limit]` keeps only the requested number of results.
- **Reusable pattern:** Cosine similarity is common in document search, recommendation systems, and semantic retrieval.

## `StudyAssistant` methods

### `StudyAssistant.__init__(text, cards=None)`

- **Purpose:** Builds the searchable study assistant from notes and optional structured fact cards.
- **How it works:** It chunks the notes, stores cards, trains a `TermNetwork`, and counts common study terms.
- **Important syntax:** `cards or []` converts a missing value (`None`) into an empty list, so later code can always iterate over `self.cards`.
- **Reusable pattern:** An initializer can prepare all indexes and models once, avoiding repeated work for every user question.

### `StudyAssistant.relevant(prompt, limit=3)`

- **Purpose:** Retrieves note sentences related to a prompt.
- **How it works:** It first finds direct term matches, then expands the query with related terms learned by `TermNetwork`.
- **Ranking rule:** Direct matches are preferred over learned related matches because exact evidence is safer for factual answers.
- **Reusable pattern:** This is a small retrieval pipeline: normalize the query, expand it, score documents, and return the top results.

### `StudyAssistant.answer(prompt)`

- **Purpose:** Answers a user question using fact cards first and note retrieval second.
- **Fact-card search:** It compares prompt terms with each card’s keywords and question terms, then selects the highest-scoring card.
- **Fallback search:** If no card matches, it calls `relevant(prompt)` and returns matching note sentences plus related terms to review.
- **Grounding behavior:** It does not ask the small generator to invent an answer. This is what prevents unrelated text drift.
- **Reusable pattern:** Use a trusted retrieval layer before any generative layer when factual accuracy matters.

### `StudyAssistant.quiz_items(limit)`

- **Purpose:** Builds the question set used by interactive quiz mode.
- **How it works:** It converts structured cards into question-answer tuples, then adds generated questions from the notes if more items are needed.
- **Important syntax:** `[(question, answer) for card in self.cards]` is a list comprehension that transforms each card into a simpler tuple.
- **Reusable pattern:** Keep source data in a rich format, then transform it into a small format that the user interface can consume.

### `StudyAssistant.learning_plan()`

- **Purpose:** Returns an ordered physiology study plan with relationships between mechanisms.
- **How it works:** It returns a multi-line string describing prerequisites and integrations rather than only listing frequent words.
- **Reusable pattern:** Hand-written domain guidance is often more reliable than automatically generated advice when the learning sequence matters.

## Study-generation functions

### `study_material(text, question_count=8)`

- **Purpose:** Extracts study topics and creates basic question-answer pairs from note sentences.
- **Definition detection:** `re.search` looks for phrases such as “is,” “are,” “means,” or “refers to.”
- **Question creation:** Definition sentences become “What is …?” questions. Other sentences become fill-in-the-blank questions by replacing a frequent word with underscores.
- **Important syntax:** `max(words_in_sentence, key=lambda word: counts[word])` selects the word with the highest frequency score. A `lambda` is a small anonymous function used only for that comparison.
- **Reusable pattern:** This is a practical baseline for automatically creating exercises from any collection of explanatory notes.

### `study_guide(text, question_count=8)`

- **Purpose:** Creates a printable study guide with priorities, questions, and an answer key.
- **How it works:** It calls `study_material`, formats each result with `enumerate`, and joins all lines with newline characters.
- **Reusable pattern:** Keep content generation separate from formatting so the same questions can power a terminal chat, web page, or exported document.

### `study_chat(text, question_count=8, cards=None)`

- **Purpose:** Runs the interactive terminal conversation.
- **How it works:** It creates a `StudyAssistant`, waits for input in a `while True` loop, checks commands, and prints the appropriate response.
- **Quiz flow:** For each `(question, answer)` pair, `enumerate` supplies a question number while `input` collects the learner’s answer.
- **Answer check:** The simple check uses lowercase substring matching. It is intentionally easy to understand and should later be replaced with a more flexible evaluator.
- **Reusable pattern:** This is a minimal command loop that can be reused for flashcards, configuration tools, or text-based games.

## Original demo model

### `MiniLanguageModel.__init__()`

- **Purpose:** Creates an empty word-level bigram model.
- **Important syntax:** `defaultdict(Counter)` automatically creates a counter the first time a token is used as a dictionary key.
- **Reusable pattern:** Nested `defaultdict` and `Counter` structures are useful for counting transitions, events, and frequencies.

### `MiniLanguageModel.train(text)`

- **Purpose:** Counts which token follows each token.
- **How it works:** `[START] + tokens` and `tokens + [END]` add boundary markers. `zip` pairs every current token with its following token.
- **Reusable pattern:** Boundary tokens are useful whenever a sequence model needs to know where input begins and ends.

### `MiniLanguageModel.next_token(current)`

- **Purpose:** Samples one likely next token from the learned counts.
- **How it works:** It selects the current token’s counter, falls back to the start-token counter, and calls `random.choices` with count-based weights.
- **Reusable pattern:** Weighted random choice is useful for simulations and simple probabilistic generators.

### `MiniLanguageModel.generate(prompt="", max_tokens=30)`

- **Purpose:** Generates a continuation from the last token of a prompt.
- **Important behavior:** The prompt is used as context, but `output` starts empty. Therefore the returned text contains only newly generated tokens and does not repeat the prompt.
- **How it works:** Each sampled token becomes the next `current` token until an end marker or token limit is reached.
- **Reusable pattern:** Separating context from generated output is important in chat interfaces and sequence generation.

## Program entry point

### `main()`

- **Purpose:** Parses command-line arguments and starts the correct mode.
- **How it works:** `argparse.ArgumentParser` defines `--study` and `--questions`. If `--study` is present, the program loads notes and cards and starts study chat; otherwise it starts the original demo.
- **Error handling:** The `try/except` block turns file and validation errors into readable command-line errors through `parser.error`.
- **Reusable pattern:** Keep command-line setup in `main` and keep the actual work in testable functions and classes.

## A useful reuse path

- To build a flashcard app, reuse `load_notes`, `sentences`, `load_cards`, and `StudyAssistant.answer`.
- To build a document search tool, reuse `content_words`, `TermNetwork.fit`, `TermNetwork.related`, and `StudyAssistant.relevant`.
- To build a web API later, call `StudyAssistant` once when the document is uploaded, then call `answer` for each request.
- To improve answer accuracy, expand `data/processed/physiology_cards.json` and add tests for each card before adding a larger generative model.
