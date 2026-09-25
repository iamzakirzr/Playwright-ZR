"""Semantic similarity: does the live bot's answer MEAN the same as the reference?

Two tiers:
  1. Metric calibration (no LLM call): proves the metric separates paraphrases from
     unrelated text on this embedding model. If this fails, the thresholds are wrong,
     not the bot.
  2. Live bot vs golden answers.
"""
import pytest
from deepeval import assert_test
from deepeval.test_case import LLMTestCase

from ai.datasets import load_golden
from ai.evaluators import cosine_similarity

GOLDEN = load_golden("cases")


class TestMetricCalibration:
    def test_paraphrase_scores_above_threshold(self, settings):
        score = cosine_similarity(
            "You have 45 days after delivery to send an item back.",
            "Returns are accepted within 45 days of delivery.",
            settings.embedding_model,
        )
        assert score >= settings.similarity_threshold, score

    def test_unrelated_text_scores_below_threshold(self, settings):
        score = cosine_similarity(
            "Customer support is open Monday to Friday.",
            "The Bike Light warranty covers battery failure.",
            settings.embedding_model,
        )
        assert score < settings.similarity_threshold, score


@pytest.mark.parametrize("case", GOLDEN, ids=[c["id"] for c in GOLDEN])
def test_answer_is_semantically_similar_to_reference(ask, similarity_metric, case):
    response = ask(case["question"], case["context"])

    test_case = LLMTestCase(
        input=case["question"],
        actual_output=response.text,
        expected_output=case["expected_answer"],
        retrieval_context=case["context"],
    )
    assert_test(test_case, [similarity_metric])
