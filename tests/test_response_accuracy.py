"""Golden-prompt tests for checking grounded study responses."""

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.mini_llm.app import StudyAssistant, autocorrect_word, load_cards


CORPUS_PATH = PROJECT_ROOT / "data" / "processed" / "physiology_training.txt"
CARDS_PATH = PROJECT_ROOT / "data" / "processed" / "physiology_cards.json"


class TrainingCorpusAccuracyTests(unittest.TestCase):
    """Check that responses contain evidence from the actual training text."""

    @classmethod
    def setUpClass(cls):
        """Load one text-only assistant so these tests exclude fact cards."""
        cls.corpus = CORPUS_PATH.read_text(encoding="utf-8")
        cls.assistant = StudyAssistant(cls.corpus)

    def assert_corpus_evidence(self, prompt, evidence):
        """Require each expected evidence phrase in both the corpus and answer."""
        answer = self.assistant.answer(prompt).lower()
        corpus = self.corpus.lower()
        self.assertNotIn("i could not find that topic", answer)
        for phrase in evidence:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase.lower(), corpus)
                self.assertIn(phrase.lower(), answer)

    def test_dhp_prompt_returns_the_dhp_ryr_mechanism(self):
        """DHP questions should retrieve RYR activation and calcium release."""
        self.assert_corpus_evidence(
            "What does DHP do?",
            ["DHP activates RYR", "release calcium"],
        )

    def test_homeostasis_prompt_returns_control_system_terms(self):
        """Homeostasis questions should connect stability to its control loop."""
        self.assert_corpus_evidence(
            "What is homeostasis?",
            ["homeostasis is the maintenance", "sensors control centers and effectors"],
        )

    def test_acetylcholinesterase_prompt_returns_signal_termination(self):
        """AChE questions should identify acetylcholine breakdown in the cleft."""
        self.assert_corpus_evidence(
            "What does acetylcholinesterase do?",
            ["acetylcholinesterase breaks down acetylcholine"],
        )

    def test_unknown_topic_does_not_invent_a_fact(self):
        """An unsupported topic should produce a grounded not-found response."""
        answer = self.assistant.answer("What is quantum chromodynamics?").lower()
        self.assertIn("could not find that topic in the notes", answer)

    def test_common_misspellings_are_normalized_before_retrieval(self):
        """Known misspellings should resolve to canonical corpus vocabulary."""
        cases = {
            "homeostatis": "homeostasis",
            "dihydropyradine": "dihydropyridine",
            "mitocondria": "mitochondria",
            "achesterase": "acetylcholinesterase",
        }
        for misspelling, expected in cases.items():
            with self.subTest(misspelling=misspelling):
                self.assertEqual(autocorrect_word(misspelling), expected)


class ReviewedCardAccuracyTests(unittest.TestCase):
    """Check precise, manually reviewed answers for important study prompts."""

    @classmethod
    def setUpClass(cls):
        """Build the production-style assistant with reviewed fact cards."""
        corpus = CORPUS_PATH.read_text(encoding="utf-8")
        cls.assistant = StudyAssistant(corpus, load_cards(CARDS_PATH))

    def assert_answer_contains(self, prompt, required_terms):
        """Require all key terms from a reviewed answer to be returned."""
        answer = self.assistant.answer(prompt).lower()
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term.lower(), answer)

    def test_action_potential_answer_contains_ion_sequence(self):
        """The action-potential card should mention sodium, potassium, and phases."""
        self.assert_answer_contains(
            "What happens during an action potential?",
            ["voltage-gated sodium", "depolarization", "potassium", "repolarize"],
        )

    def test_adh_answer_contains_water_reabsorption(self):
        """The ADH card should connect hormone action to collecting ducts."""
        self.assert_answer_contains(
            "How does ADH affect the kidney?",
            ["water permeability", "collecting ducts", "concentrated urine"],
        )

    def test_aChE_answer_does_not_repeat_the_previous_inaccuracy(self):
        """The reviewed answer must not claim AChE stops a propagating action potential."""
        answer = self.assistant.answer(
            "What ends acetylcholine signaling at the neuromuscular junction?"
        ).lower()
        self.assertIn("breaks acetylcholine down", answer)
        self.assertIn("does not directly stop an action potential", answer)

    def test_misspelled_dhp_prompt_still_finds_the_reviewed_fact(self):
        """A misspelled receptor name should still reach the DHP/RYR card."""
        answer = self.assistant.answer(
            "What does the dihydropyradine receptor do?"
        ).lower()
        self.assertIn("ryr", answer)
        self.assertIn("calcium", answer)

    def test_misspelled_ache_prompt_still_finds_the_reviewed_fact(self):
        """A misspelled acetylcholinesterase query should remain grounded."""
        answer = self.assistant.answer("What does achesterase do?").lower()
        self.assertIn("breaks acetylcholine down", answer)


if __name__ == "__main__":
    unittest.main()
