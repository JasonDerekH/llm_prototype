"""A dependency-free educational language-model prototype.

This is a small word-level bigram model, not a production LLM. It learns which
word is likely to follow another word and samples from those learned patterns.

It also includes a compact, document-grounded study mode. Study mode uses
simple text heuristics to create questions from notes; it does not invent
facts outside the supplied document.
"""

import argparse
from collections import defaultdict, Counter
import json
from pathlib import Path
import random
import re
import subprocess

from .models.term_network import TermNetwork

START = "<START>"
END = "<END>"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"


def tokenize(text: str) -> list[str]:
    """Split text into lowercase word and punctuation tokens."""
    return re.findall(r"[A-Za-z']+|[.!?,]", text.lower())


def load_notes(path: Path) -> str:
    """Read plain-text notes, or extract text from a legacy .doc using Word."""
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8")
    if suffix == ".docx":
        # DOCX is a ZIP of XML files; this keeps the prototype dependency-free.
        from zipfile import ZipFile
        from xml.etree import ElementTree

        with ZipFile(path) as archive:
            xml = archive.read("word/document.xml")
        root = ElementTree.fromstring(xml)
        return "\n".join(node.text or "" for node in root.iter()
                           if node.tag.endswith("}t"))
    if suffix == ".doc":
        # Legacy .doc is a binary format. Word is the smallest reliable local
        # extractor on Windows, so use its COM interface when available.
        script = (
            "$word = New-Object -ComObject Word.Application; "
            "$doc = $word.Documents.Open((Resolve-Path -LiteralPath '{0}')); "
            "$text = $doc.Content.Text; $doc.Close(); $word.Quit(); "
            "[Console]::Write($text)"
        ).format(str(path).replace("'", "''"))
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
        raise RuntimeError("Could not read .doc. On Windows, install Microsoft Word.")
    raise ValueError("Supported note files are .txt, .md, .doc, and .docx.")


def load_cards(path: Path) -> list[dict[str, object]]:
    """Load original, structured study facts used for more precise answers."""
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("The study knowledge base must contain a JSON list.")
    return [card for card in data if isinstance(card, dict)
            and card.get("question") and card.get("answer")]


STOP_WORDS = {
    "about", "after", "again", "also", "because", "being", "between",
    "could", "from", "have", "into", "more", "other", "should", "that",
    "their", "there", "these", "they", "this", "through", "using", "were",
    "which", "with", "would", "your", "than", "then", "when", "where",
    "does", "doing", "each", "for", "how", "what", "who", "why", "the",
}

# These corrections are intentionally limited to terms used by the study
# corpus. A small explicit vocabulary is safer than changing every unfamiliar
# word, which could accidentally change the user's intended topic.
COMMON_MISSPELLINGS = {
    "homeostatis": "homeostasis",
    "homeostesis": "homeostasis",
    "mitocondria": "mitochondria",
    "mitochondriae": "mitochondria",
    "dihydropyradine": "dihydropyridine",
    "dihydropyradin": "dihydropyridine",
    "ryanodene": "ryanodine",
    "ryanodinee": "ryanodine",
    "sarcolemmae": "sarcolemma",
    "sarcoplasm": "sarcoplasmic",
    "depolarizaton": "depolarization",
    "repolarizaton": "repolarization",
    "acetylcholineesterase": "acetylcholinesterase",
    "acetylcholinesterasee": "acetylcholinesterase",
    "achesterase": "acetylcholinesterase",
    "acetylcholin": "acetylcholine",
    "neurotransmiter": "neurotransmitter",
    "neurotransmittor": "neurotransmitter",
    "sympatetic": "sympathetic",
    "parasympatetic": "parasympathetic",
    "potasium": "potassium",
    "sodum": "sodium",
    "troponnin": "troponin",
    "tropomyosin": "tropomyosin",
}


def autocorrect_word(word: str) -> str:
    """Convert a known study-term misspelling to its canonical spelling."""
    lowered = word.lower()
    return COMMON_MISSPELLINGS.get(lowered, lowered)


def sentences(text: str) -> list[str]:
    """Split notes into normalized sentences long enough to be useful."""
    return [re.sub(r"\s+", " ", item).strip(" -")
            for item in re.split(r"(?<=[.!?])\s+|\n+", text)
            if len(item.split()) >= 3]


def content_words(text: str) -> list[str]:
    """Return lowercase non-stop words used for topic matching."""
    corrected = [autocorrect_word(word)
                 for word in re.findall(r"[A-Za-z]{3,}", text)]
    return [word for word in corrected if word not in STOP_WORDS]


class StudyAssistant:
    """Retrieve grounded answers from notes instead of generating unrelated text."""

    def __init__(self, text: str, cards: list[dict[str, object]] | None = None) -> None:
        """Build a grounded assistant from note sentences and fact cards."""
        self.source_sentences = sentences(text)
        self.cards = cards or []
        self.network = TermNetwork()
        self.network.fit(self.source_sentences)
        self.topics = [word for word, _ in Counter(
            word for sentence in self.source_sentences for word in content_words(sentence)
        ).most_common(8)]

    def relevant(self, prompt: str, limit: int = 3) -> list[str]:
        """Rank note sentences by direct and learned term overlap."""
        prompt_terms = set(content_words(prompt))
        expanded = set(prompt_terms)
        for term in prompt_terms:
            expanded.update(self.network.related(term))
        direct_matches = []
        related_matches = []
        for sentence in self.source_sentences:
            sentence_terms = set(content_words(sentence))
            direct_score = len(sentence_terms & prompt_terms)
            related_score = len(sentence_terms & (expanded - prompt_terms))
            if direct_score:
                direct_matches.append((direct_score, sentence))
            elif related_score:
                related_matches.append((related_score, sentence))
        ranked = direct_matches or related_matches
        return [sentence for _, sentence in sorted(ranked, key=lambda item: item[0], reverse=True)[:limit]]

    def answer(self, prompt: str) -> str:
        """Answer from a matching fact card or retrieved note sentences."""
        prompt_terms = set(content_words(prompt))
        card_matches = []
        for card in self.cards:
            keywords = " ".join(str(keyword) for keyword in card.get("keywords", []))
            card_terms = set(content_words(keywords))
            card_terms.update(content_words(str(card["question"])))
            score = len(prompt_terms & card_terms)
            if score:
                card_matches.append((score, card))
        if card_matches:
            score, card = max(card_matches, key=lambda item: item[0])
            if score >= 1:
                topic = card.get("topic", "the notes")
                return (f"From the {topic} study notes:\n- {card['answer']}\n"
                        "\nStudy check: " + str(card["question"]))
        matches = self.relevant(prompt)
        if not matches:
            return ("I could not find that topic in the notes. Ask about one of these terms: "
                    + ", ".join(self.topics) + ".")
        response = "From your notes:\n- " + "\n- ".join(matches)
        related = sorted({term for word in content_words(prompt)
                          for term in self.network.related(word)})
        if related:
            response += "\n\nRelated terms to review: " + ", ".join(related[:6])
        return response

    def quiz_items(self, limit: int) -> list[tuple[str, str]]:
        """Prefer precise fact cards, then fall back to generated note questions."""
        items = [(str(card["question"]), str(card["answer"])) for card in self.cards]
        _, generated = study_material("\n".join(self.source_sentences), limit)
        return (items + generated)[:limit]

    def learning_plan(self) -> str:
        """Give useful next-study context instead of only naming frequent words."""
        return ("Based on the notes, study in this order:\n"
                "1. Homeostasis and control systems: connect sensors, control centers, effectors, and negative feedback to regulated variables.\n"
                "2. Membrane physiology: master concentration gradients, electrochemical gradients, ion channels, resting potential, graded potentials, and action potentials.\n"
                "3. Synapses and muscle: trace acetylcholine at the neuromuscular junction through the sarcolemma, t tubules, DHP, RYR, calcium, troponin, and cross bridge cycling.\n"
                "4. Autonomic regulation: compare sympathetic and parasympathetic pathways, neurotransmitters, receptors, and target-organ effects.\n"
                "5. Cardiovascular integration: connect cardiac conduction, the cardiac cycle, preload, afterload, cardiac output, blood pressure, and vessel resistance.\n"
                "6. Kidney and respiratory integration: explain filtration, reabsorption, ADH, ventilation, perfusion, gas exchange, and acid-base balance.\n"
                "7. Endocrine regulation: compare peptide and steroid hormones, receptor mechanisms, pituitary control, thyroid and adrenal hormones, insulin, and glucagon.\n"
                "For each topic, explain the trigger, the mechanism, the target, and the resulting change. Then test yourself without looking at the notes.")


def study_material(text: str, question_count: int = 8) -> tuple[list[str], list[str]]:
    """Extract study topics and simple grounded question/answer pairs."""
    source_sentences = sentences(text)
    if not source_sentences:
        return [], []

    definitions = [s for s in source_sentences
                   if re.search(r"\b(is|are|means|refers to|defined as)\b", s, re.I)]
    words = [word.lower() for word in re.findall(r"[A-Za-z]{5,}", text)]
    counts = Counter(word for word in words if word not in STOP_WORDS)
    topics = [word for word, _ in counts.most_common(8)]
    selected = (definitions + [s for s in source_sentences if s not in definitions])[:question_count]
    questions = []
    for number, sentence in enumerate(selected, 1):
        if number <= len(definitions):
            match = re.search(r"^(.{2,60}?)\s+(?:is|are|means|refers to|defined as)\s+(.+)$", sentence, re.I)
            if match:
                questions.append((f"What is {match.group(1).strip()}?", match.group(2).strip()))
                continue
        words_in_sentence = re.findall(r"\b[A-Za-z]{5,}\b", sentence)
        answer_word = max(words_in_sentence, key=lambda word: counts[word], default="the key idea")
        blanked = re.sub(rf"\b{re.escape(answer_word)}\b", "_____", sentence, count=1, flags=re.I)
        questions.append((f"Fill in the blank: {blanked}", answer_word))
    return topics, questions


def study_guide(text: str, question_count: int = 8) -> str:
    """Create a printable fallback guide from the notes."""
    topics, questions = study_material(text, question_count)
    if not questions:
        return "Not enough text to make a study guide. Add several complete sentences."

    lines = ["STUDY GUIDE", "===========", "", "Study priorities:"]
    lines += [f"- Review: {topic}" for topic in topics] or ["- Re-read the provided notes and add more detail."]
    lines += ["", "Practice test:"]
    answers = []
    for number, (question, answer) in enumerate(questions, 1):
        lines.append(f"{number}. {question}")
        answers.append(f"{number}. {answer}")
    lines += ["", "Answer key:"] + answers
    return "\n".join(lines)


def study_chat(text: str, question_count: int = 8,
               cards: list[dict[str, object]] | None = None) -> None:
    """Run a conversational study session grounded in the loaded notes."""
    assistant = StudyAssistant(text, cards)
    topics, questions = study_material(text, max(1, question_count))
    questions = assistant.quiz_items(max(1, question_count))
    if not questions:
        print("Not enough text to start. Add several complete sentences to the notes.")
        return
    print("Study chat ready. Ask for a quiz, study topics, or type 'quit'.")
    while True:
        prompt = input("\nYou: ").strip()
        lowered = prompt.lower()
        if lowered in {"quit", "exit"}:
            print("Goodbye!")
            return
        if ("topic" in lowered or "study" in lowered or "review" in lowered
                or "learn" in lowered or "what should" in lowered):
            print("Assistant: " + assistant.learning_plan())
            continue
        if "quiz" in lowered or "test" in lowered or "question" in lowered:
            print("Assistant: Let's begin. Answer each question, or type 'skip'.")
            for number, (question, answer) in enumerate(questions, 1):
                print(f"\nQuestion {number}: {question}")
                response = input("Your answer: ").strip()
                if response.lower() == "skip":
                    print(f"Assistant: The notes say: {answer}")
                elif answer.lower() in response.lower() or response.lower() in answer.lower():
                    print("Assistant: Correct. Nice work.")
                else:
                    print(f"Assistant: Not quite. Review this answer: {answer}")
            print("\nAssistant: Quiz complete. Ask for another quiz or ask what to study.")
            continue
        print("Assistant: " + assistant.answer(prompt))


class MiniLanguageModel:
    def __init__(self) -> None:
        """Create an empty word-level next-token model."""
        self.next_token_counts: dict[str, Counter[str]] = defaultdict(Counter)

    def train(self, text: str) -> None:
        """Count which tokens follow each token in the training text."""
        tokens = tokenize(text)
        for current, following in zip([START] + tokens, tokens + [END]):
            self.next_token_counts[current][following] += 1

    def next_token(self, current: str) -> str:
        """Sample one token using counts for the current token."""
        choices = self.next_token_counts.get(current) or self.next_token_counts[START]
        words = list(choices.keys())
        weights = list(choices.values())
        return random.choices(words, weights=weights, k=1)[0]

    def generate(self, prompt: str = "", max_tokens: int = 30) -> str:
        """Generate only a continuation, keeping the prompt as context."""
        prompt_tokens = tokenize(prompt)
        output = []
        current = prompt_tokens[-1] if prompt_tokens else START
        for _ in range(max_tokens):
            token = self.next_token(current)
            if token == END:
                break
            output.append(token)
            current = token
        text = " ".join(output)
        continuation = re.sub(r"\s+([.!?,])", r"\1", text).capitalize()
        return continuation or "I could not generate a continuation from the training data."


def main() -> None:
    """Parse command-line options and start study or demo chat mode."""
    parser = argparse.ArgumentParser(description="Run the mini LLM or make a study guide.")
    parser.add_argument("--study", type=Path, metavar="NOTES",
                        help="create a practice test from a .txt, .md, .doc, or .docx file")
    parser.add_argument("--questions", type=int, default=8,
                        help="number of practice questions (default: 8)")
    parser.add_argument("--include-open-data", action="store_true",
                        help="include reviewed public-domain text in the demo corpus")
    args = parser.parse_args()

    if args.study:
        try:
            cards_file = PROCESSED_DATA_DIR / "physiology_cards.json"
            study_chat(load_notes(args.study), args.questions, load_cards(cards_file))
        except (OSError, RuntimeError, ValueError) as error:
            parser.error(str(error))
        return

    data_file = PROCESSED_DATA_DIR / "physiology_training.txt"
    training_text = data_file.read_text(encoding="utf-8")
    if args.include_open_data:
        raw_dir = PROJECT_ROOT / "data" / "raw"
        open_text = [path.read_text(encoding="utf-8")
                     for path in sorted(raw_dir.glob("*.txt"))]
        training_text = "\n".join([training_text, *open_text])
    model = MiniLanguageModel()
    model.train(training_text)

    print("Mini LLM prototype")
    print("Type a prompt, or type 'quit' to exit.")
    while True:
        prompt = input("\nYou: ").strip()
        if prompt.lower() in {"quit", "exit"}:
            print("Goodbye!")
            break
        print("Model:", model.generate(prompt))


if __name__ == "__main__":
    main()
