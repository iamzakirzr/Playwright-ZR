"""Production RAG metric suite: the metrics teams track on LLM dashboards.

Three tiers, decided by **judge calibration** (a judged metric is only trusted
with a judge that passes calibration for it):

1. Deterministic, per case (gating): the facts the question strictly needs.
2. Default 3B judge: G-Eval completeness (calibrated below). Faithfulness
   lives in ``test_faithfulness.py``.
3. Strong 7B judge (opt-in): answer relevancy, correctness, hallucination and
   contextual precision / recall / relevancy. With the 3B judge these failed
   calibration: an on-topic answer scored 0.25 on relevancy; correctness gave a
   flat 0.6 to right and wrong answers; hallucination was inverted (correct
   1.0, wrong 0.0); and contextual recall scored 0.33 on a *perfect* retrieval
   (all three shipping passages in the top 3), passing locally and failing in
   CI on identical inputs. Retrieval quality is gated deterministically by the
   IR metrics in ``tests/ai/search``.

Helpfulness (mentioning *every* useful fact, not just the essential one) is
tracked at the **dataset level** against a recorded baseline. The 1.5B model
reliably gives the essential fact but drops extras (e.g. the $4.99 fee when
asked "Is shipping free?"), and no prompt variant fixed that. The baseline
makes the gap visible and fails if it gets worse, without failing forever on a
known model limitation.
"""

import pytest
from deepeval import assert_test
from deepeval.test_case import LLMTestCase

from ai.datasets import golden_case, load_golden
from ai.evaluators import KeywordCoverageMetric

GOLDEN = load_golden("cases")
IDS = [c["id"] for c in GOLDEN]


def _case(entry: dict, answer: str, contexts: list[str] | None = None) -> LLMTestCase:
    """Build a DeepEval test case from a golden entry and a live answer."""
    contexts = contexts or entry["context"]
    return LLMTestCase(
        input=entry["question"],
        actual_output=answer,
        expected_output=entry["expected_answer"],
        retrieval_context=contexts,
        context=contexts,
    )


# --------------------------------------------------------------------------- #
# Tier 1: deterministic, per case
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("case", GOLDEN, ids=IDS)
def test_answer_contains_every_required_fact(ask, case):
    """Gating: every fact the question strictly needs is in the answer."""
    answer = ask(case["question"], case["context"]).text

    assert_test(_case(case, answer), [KeywordCoverageMetric(case["required_facts"], threshold=1.0)])


def test_helpful_fact_coverage_within_baseline(ask, settings):
    """Dataset-level helpfulness: mean coverage of all useful facts stays at or above the recorded baseline."""
    rows = []
    for case in GOLDEN:
        metric = KeywordCoverageMetric(case["helpful_facts"])
        metric.measure(LLMTestCase(input=case["question"], actual_output=ask(case["question"], case["context"]).text))
        rows.append((case["id"], metric.score, metric.reason))
    mean = sum(score for _, score, _ in rows) / len(rows)

    report = "\n".join(f"  {cid}: {score:.2f} {reason}" for cid, score, reason in rows)
    assert mean >= settings.min_mean_helpful_coverage, f"mean helpful coverage {mean:.2f}\n{report}"


# --------------------------------------------------------------------------- #
# Tier 2: default judge (calibrated)
# --------------------------------------------------------------------------- #
class TestCompletenessCalibration:
    """The completeness judge must separate complete from incomplete answers."""

    def test_complete_reference_answer_passes(self, metrics, settings):
        """The human-written reference answer is judged complete."""
        case = golden_case("warranty")
        metric = metrics.completeness(settings.completeness_threshold)
        metric.measure(_case(case, case["expected_answer"]))

        assert metric.is_successful(), f"completeness={metric.score}: {metric.reason}"

    def test_incomplete_answer_is_penalised(self, metrics, settings):
        """An answer stating only the free-shipping rule is judged incomplete."""
        case = golden_case("shipping-cost")
        metric = metrics.completeness(settings.completeness_threshold)
        metric.measure(_case(case, "Orders of $75 or more ship free."))

        assert not metric.is_successful(), f"completeness={metric.score}: {metric.reason}"


def test_judged_completeness_within_baseline(ask, metrics, settings):
    """Dataset-level G-Eval completeness stays at or above the recorded baseline (prints per-case scores)."""
    rows = []
    for case in GOLDEN:
        metric = metrics.completeness(settings.completeness_threshold)
        metric.measure(_case(case, ask(case["question"], case["context"]).text))
        rows.append((case["id"], metric.score))
    mean = sum(score for _, score in rows) / len(rows)

    assert mean >= settings.min_mean_completeness, f"mean completeness {mean:.2f}: {rows}"


# --------------------------------------------------------------------------- #
# Tier 3: strong judge (opt-in: needs STRONG_JUDGE_MODEL, e.g. qwen2.5:7b)
# --------------------------------------------------------------------------- #
class TestStrongJudgeCalibration:
    """Calibrate the strong judge on hand-written answers before trusting it."""

    WRONG = "The Bike Light has a 5-year warranty that covers water damage and accidental drops."

    def test_relevancy_and_correctness_pass_on_reference(self, strong_metrics):
        """The reference answer is judged relevant and correct."""
        case = golden_case("warranty")

        assert_test(_case(case, case["expected_answer"]), [strong_metrics.answer_relevancy(), strong_metrics.correctness()])

    def test_wrong_answer_fails_correctness_and_hallucination(self, strong_metrics):
        """A contradicting answer is judged incorrect and hallucinated."""
        case = golden_case("warranty")
        correctness, hallucination = strong_metrics.correctness(), strong_metrics.hallucination()
        test_case = _case(case, self.WRONG)
        correctness.measure(test_case)
        hallucination.measure(test_case)

        assert not correctness.is_successful(), f"correctness={correctness.score}"
        assert not hallucination.is_successful(), f"hallucination={hallucination.score}"


@pytest.mark.parametrize("case", GOLDEN, ids=IDS)
def test_answer_relevancy_correctness_hallucination(ask, strong_metrics, case):
    """The live answer is on-topic, agrees with the reference, and doesn't contradict the context."""
    answer = ask(case["question"], case["context"]).text

    assert_test(
        _case(case, answer),
        [strong_metrics.answer_relevancy(), strong_metrics.correctness(), strong_metrics.hallucination()],
    )


@pytest.mark.parametrize("case", GOLDEN[:2], ids=IDS[:2])
def test_retrieval_context_quality_end_to_end(rag_pipeline, strong_metrics, case):
    """Contextual precision, recall and relevancy on passages the live search really retrieved."""
    result = rag_pipeline.answer(case["question"])

    assert_test(
        _case(case, result.text, result.contexts),
        [
            strong_metrics.contextual_precision(),
            strong_metrics.contextual_recall(),
            strong_metrics.contextual_relevancy(threshold=0.3),
        ],
    )
