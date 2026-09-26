"""Traditional reference metrics (Hugging Face ``evaluate``: ROUGE, BLEU) and when *not* to use them.

Offline: no chatbot; only the metric scripts download from the Hugging Face Hub once.
The core lesson is a calibration fact, asserted on every run: n-gram overlap punishes correct
paraphrases, which embedding similarity accepts. So these metrics gate wording-sensitive
outputs (templates, extractive summaries) and are reported, not gated, for free-form answers.
"""

import pytest
from deepeval import assert_test
from deepeval.test_case import LLMTestCase

from ai.evaluators import BleuMetric, RougeMetric, bleu_score, cosine_similarity, rouge_scores

REFERENCE = "Returns are accepted within 45 days of delivery."
PARAPHRASE = "You have 45 days after delivery to send an item back."
UNRELATED = "Customer support is open Monday to Friday."


class TestCalibration:
    """What the scores mean on known inputs."""

    def test_identical_text_scores_one(self):
        """An exact copy is a perfect match for both metrics."""
        assert rouge_scores(REFERENCE, REFERENCE)["rougeL"] == pytest.approx(1.0)
        assert bleu_score(REFERENCE, REFERENCE) == pytest.approx(1.0)

    def test_unrelated_text_scores_near_zero(self):
        """No shared content, (almost) no overlap."""
        assert rouge_scores(UNRELATED, REFERENCE)["rougeL"] < 0.1
        assert bleu_score(UNRELATED, REFERENCE) < 0.1

    def test_ngram_metrics_punish_a_correct_paraphrase(self, settings):
        """The reason not to gate LLM answers on BLEU/ROUGE: same meaning, low overlap.

        Measured: ROUGE-L 0.32, BLEU 0.08, cosine similarity above the 0.70 threshold.
        """
        assert rouge_scores(PARAPHRASE, REFERENCE)["rougeL"] < 0.5
        assert bleu_score(PARAPHRASE, REFERENCE) < 0.2
        assert cosine_similarity(PARAPHRASE, REFERENCE, settings.embedding_model) >= settings.similarity_threshold

    def test_rouge_variants_are_ordered(self):
        """Bigram overlap (ROUGE-2) can't exceed unigram overlap (ROUGE-1)."""
        scores = rouge_scores(PARAPHRASE, REFERENCE)

        assert scores["rouge2"] <= scores["rouge1"]


def test_local_backends_match_hugging_face_evaluate():
    """The offline scorers give exactly what ``evaluate.load("rouge"/"sacrebleu")`` reports (needs the Hub once)."""
    from ai.evaluators.reference_metrics import load_hf_metric

    hf_rouge = load_hf_metric("rouge").compute(predictions=[PARAPHRASE], references=[REFERENCE])
    hf_bleu = load_hf_metric("sacrebleu").compute(predictions=[PARAPHRASE], references=[[REFERENCE]])["score"] / 100
    local = rouge_scores(PARAPHRASE, REFERENCE)

    for key in ("rouge1", "rouge2", "rougeL"):
        assert local[key] == pytest.approx(hf_rouge[key])
    assert bleu_score(PARAPHRASE, REFERENCE) == pytest.approx(hf_bleu)


class TestAsDeepEvalMetrics:
    """The wrappers plug into ``assert_test`` like any other metric."""

    def test_templated_message_passes_rouge_and_bleu(self):
        """Where wording is the requirement (a templated cart summary), overlap metrics fit."""
        case = LLMTestCase(
            input="show my cart",
            actual_output="Your cart: 2 x Sauce Labs Backpack. Total $59.98.",
            expected_output="Your cart: 2 x Sauce Labs Backpack. Total $59.98.",
        )

        assert_test(case, [RougeMetric(threshold=0.95), BleuMetric(threshold=0.95)])

    def test_changed_template_fails(self):
        """A reworded template is caught: this is the regression these metrics are good at."""
        metric = RougeMetric(threshold=0.9)
        case = LLMTestCase(
            input="show my cart",
            actual_output="Items in basket: Backpack (2). You owe $59.98.",
            expected_output="Your cart: 2 x Sauce Labs Backpack. Total $59.98.",
        )

        metric.measure(case)

        assert not metric.is_successful()

    def test_missing_reference_is_an_error(self):
        """Reference metrics need ``expected_output``; failing loudly beats scoring 0."""
        with pytest.raises(ValueError, match="expected_output"):
            RougeMetric().measure(LLMTestCase(input="q", actual_output="a"))
