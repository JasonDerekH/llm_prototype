"""A compact trainable term-association network for grounded retrieval."""

import math
import random


STOP_WORDS = {
    "about", "after", "again", "also", "because", "being", "between",
    "could", "from", "have", "into", "more", "other", "should", "that",
    "their", "there", "these", "they", "this", "through", "using", "were",
    "which", "with", "would", "your", "than", "then", "when", "where",
    "does", "doing", "each", "for", "how", "what", "who", "why", "the",
}


def content_words(text: str) -> list[str]:
    """Return meaningful lowercase words used as network vocabulary."""
    import re

    return [word.lower() for word in re.findall(r"[A-Za-z]{3,}", text)
            if word.lower() not in STOP_WORDS]


class TermNetwork:
    """Learn small vectors that bring co-occurring terms closer together.

    This is an educational embedding layer, not a replacement for a
    production language model. Its output is used to expand retrieval terms
    before the study assistant selects grounded note sentences.
    """

    def __init__(self, dimensions: int = 8, epochs: int = 20) -> None:
        """Create a deterministic term-embedding network."""
        self.dimensions = dimensions
        self.epochs = epochs
        self.vectors: dict[str, list[float]] = {}
        self.random = random.Random(7)

    def fit(self, source_sentences: list[str]) -> None:
        """Train term vectors from words that share a sentence."""
        vocabulary = sorted({word for sentence in source_sentences
                             for word in content_words(sentence)})
        self.vectors = {
            word: [self.random.uniform(-0.1, 0.1) for _ in range(self.dimensions)]
            for word in vocabulary
        }
        pairs = []
        for sentence in source_sentences:
            words = list(dict.fromkeys(content_words(sentence)))
            pairs.extend((left, right) for left in words for right in words
                          if left != right)
        if not pairs:
            return
        for _ in range(self.epochs):
            for left, right in pairs:
                self._learn(left, right, 1.0)
                negative = self.random.choice(vocabulary)
                if negative != left:
                    self._learn(left, negative, 0.0)

    def _learn(self, left: str, right: str, target: float) -> None:
        """Apply one gradient update to a term pair."""
        first, second = self.vectors[left], self.vectors[right]
        score = sum(a * b for a, b in zip(first, second))
        error = score - target
        rate = 0.025
        for index in range(self.dimensions):
            first_value, second_value = first[index], second[index]
            first[index] -= rate * error * second_value
            second[index] -= rate * error * first_value

    def related(self, term: str, limit: int = 3) -> list[str]:
        """Return terms with the highest cosine similarity to a term."""
        if term not in self.vectors:
            return []
        source = self.vectors[term]
        source_length = math.sqrt(sum(value * value for value in source)) or 1
        scores = []
        for candidate, vector in self.vectors.items():
            if candidate == term:
                continue
            length = math.sqrt(sum(value * value for value in vector)) or 1
            similarity = sum(a * b for a, b in zip(source, vector)) / (source_length * length)
            scores.append((similarity, candidate))
        return [candidate for _, candidate in sorted(scores, reverse=True)[:limit]]
