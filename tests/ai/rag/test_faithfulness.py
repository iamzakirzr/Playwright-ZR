"""Faithfulness: is every claim in the bot's answer supported by the retrieval context?

DeepEval's FaithfulnessMetric extracts claims from the answer and asks the judge
LLM whether each is supported or contradicted by the context. Score = supported / total.

Tier 1 (judge calibration) runs the metric on hand-written answers, so we know the
judge can tell a faithful answer from a hallucinated one BEFORE we trust it on
live output. A judge that passes everything is worse than no test.
"""

import pytest
from deepeval import assert_test
from deepeval.test_case import LLMTestCase

from ai.datasets import golden_case, load_golden

GOLDEN = load_golden("cases")
RETURNS = golden_case("returns-window")


class TestJudgeCalibration:
    """Prove the judge discriminates before trusting it on live output."""

    def test_faithful_reference_answer_passes(self, faithfulness_metric):
        """The human-written reference answer must be judged faithful."""
        faithfulness_metric.measure(
            LLMTestCase(
                input=RETURNS["question"],
                actual_output=RETURNS["expected_answer"],
                retrieval_context=RETURNS["context"],
            )
        )
        assert faithfulness_metric.is_successful(), faithfulness_metric.reason

    def test_hallucinated_answer_is_caught(self, faithfulness_metric):
        """An answer that contradicts the context must be judged unfaithful."""
        faithfulness_metric.measure(
            LLMTestCase(
                input=RETURNS["question"],
                actual_output="You can return items within 90 days, and no receipt or packaging is needed.",
                retrieval_context=RETURNS["context"],
            )
        )
        assert not faithfulness_metric.is_successful(), (
            f"Judge failed to flag a contradiction (score={faithfulness_metric.score}): {faithfulness_metric.reason}"
        )


@pytest.mark.parametrize("case", GOLDEN, ids=[c["id"] for c in GOLDEN])
def test_live_answer_is_faithful_to_context(ask, faithfulness_metric, case):
    """Every claim in the live answer must be supported by the supplied context."""
    response = ask(case["question"], case["context"])

    test_case = LLMTestCase(
        input=case["question"],
        actual_output=response.text,
        retrieval_context=case["context"],
    )
    assert_test(test_case, [faithfulness_metric])
