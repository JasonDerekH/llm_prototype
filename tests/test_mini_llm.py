"""Small standard-library tests that collaborators can extend."""

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.mini_llm.app import MiniLanguageModel, StudyAssistant, TermNetwork, sentences, tokenize


class TextTests(unittest.TestCase):
    """Verify the basic text normalization used by every model component."""

    def test_tokenize_keeps_words_and_punctuation(self):
        self.assertEqual(tokenize("DHP opens RYR."), ["dhp", "opens", "ryr", "."])

    def test_sentences_discards_very_short_fragments(self):
        self.assertEqual(sentences("Hi. The sarcomere produces movement."),
                         ["The sarcomere produces movement."])


class ModelTests(unittest.TestCase):
    """Verify that both the language demo and term network can train."""

    def test_bigram_model_generates_a_continuation(self):
        model = MiniLanguageModel()
        model.train("A neuron sends a signal. A neuron receives input.")
        result = model.generate("neuron", max_tokens=4)
        self.assertTrue(result)

    def test_term_network_returns_related_terms(self):
        network = TermNetwork(dimensions=4, epochs=2)
        network.fit(["DHP opens the RYR.", "The RYR releases calcium."])
        self.assertIsInstance(network.related("dhp"), list)


class StudyAssistantTests(unittest.TestCase):
    """Verify that study answers stay connected to supplied notes."""

    def test_answer_uses_a_matching_note_sentence(self):
        assistant = StudyAssistant("DHP opens the RYR channel.")
        answer = assistant.answer("What does DHP do?")
        self.assertIn("DHP", answer)
        self.assertIn("RYR", answer)


if __name__ == "__main__":
    unittest.main()
