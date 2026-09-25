"""Production RAG metric suite: the metrics teams track on LLM dashboards.

Each metric targets a different failure:

* answer relevancy: the answer wanders off the question
* completeness (G-Eval) + keyword coverage: required facts are omitted
* correctness (G-Eval): the answer disagrees with the reference
* hallucination: the answer contradicts the ground-truth context
* contextual precision / recall / relevancy: *retrieval* quality, judged end-to-end
  on the live RAG pipeline (search, then answer)

Keyword coverage is the deterministic twin of G-Eval completeness. When they
disagree, investigate before trusting either.
"""
import pytest
from deepeval import assert_test
from deepeval.test_case import LLMTestCase

from ai.datasets import golden_case, load_golden
from ai.evaluators import KeywordCoverageMetric

GOLDEN = load_golden("cases")
IDS = [c["id"] for c in GOLDEN]


def _case(entry: dict, answer: str) -> LLMTestCase:
    """Build a DeepEval test case from a golden entry and a live answer."""
    return LLMTestCase(
        input=entry["question"],
        actual_output=answer,
        expected_output=entry["expected_answer"],
        retrieval_context=entry["context"],
        context=entry["context"],
    )


@pytest.mark.parametrize("case", GOLDEN, ids=IDS)
def test_answer_covers_required_facts(ask, case):
    """Deterministic completeness: every required fact string appears in the answer."""
    answer = ask(case["question"], case["context"]).text

    assert_test(_case(case, answer), [KeywordCoverageMetric(case["required_facts"], threshold=0.75)])


@pytest.mark.parametrize("case", GOLDEN, ids=IDS)
def test_answer_relevancy(ask, metrics, case):
    """The answer's statements must address the question asked."""
    answer = ask(case["question"], case["context"]).text

    assert_test(_case(case, answer), [metrics.answer_relevancy()])


@pytest.mark.parametrize("case", GOLDEN, ids=IDS)
def test_answer_correctness_and_completeness(ask, metrics, case):
    """G-Eval rubrics: agrees with the reference, and omits no needed fact."""
    answer = ask(case["question"], case["context"]).text

    assert_test(_case(case, answer), [metrics.correctness(), metrics.completeness()])


def test_no_hallucination_against_ground_truth(ask, metrics):
    """HallucinationMetric: the answer must not contradict the ground-truth context."""
    case = golden_case("warranty")
    answer = ask(case["question"], case["context"]).text

    assert_test(_case(case, answer), [metrics.hallucination()])


class TestCompletenessCalibration:
    """The completeness judge must fail an answer that omits facts, or it proves nothing."""

    def test_incomplete_answer_is_penalised(self, metrics):
        """An answer that states only the free-shipping rule must score low on completeness."""
        case = golden_case("shipping-cost")
        metric = metrics.completeness()
        metric.measure(_case(case, "Orders of $75 or more ship free."))

        assert not metric.is_successful(), f"completeness={metric.score}: {metric.reason}"


@pytest.mark.parametrize("case", GOLDEN[:2], ids=IDS[:2])
def test_retrieval_context_quality_end_to_end(rag_pipeline, metrics, case):
    """Contextual precision, recall and relevancy on passages the live search really retrieved."""
    result = rag_pipeline.answer(case["question"])
    test_case = LLMTestCase(
        input=case["question"],
        actual_output=result.text,
        expected_output=case["expected_answer"],
        retrieval_context=result.contexts,
    )

    assert_test(
        test_case,
        [metrics.contextual_precision(), metrics.contextual_recall(), metrics.contextual_relevancy(threshold=0.3)],
    )
