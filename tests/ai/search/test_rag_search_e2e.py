"""End-to-end AI search: question → hybrid retrieval → grounded answer (live model).

Checks the seam between search and generation: the answer must be supported
by the passages that were *actually retrieved*, and the pipeline must abstain
without calling the LLM when search finds nothing relevant.
"""

import pytest
from deepeval import assert_test
from deepeval.test_case import LLMTestCase

from ai.chatbot import ScriptedChatbot
from ai.evaluators import KeywordCoverageMetric
from ai.search import NO_ANSWER, RagPipeline

CASES = [
    ("Do you accept PayPal?", "payments-1", ["PayPal"]),
    ("How much is express shipping?", "shipping-3", ["$14.99"]),
    ("Is water damage covered by the Bike Light warranty?", "warranty-3", ["water damage"]),
]


@pytest.mark.parametrize(("question", "expected_doc", "facts"), CASES, ids=[c[1] for c in CASES])
def test_rag_retrieves_evidence_and_answers_from_it(rag_pipeline, question, expected_doc, facts):
    """The right passage is retrieved and its key fact appears in the answer."""
    result = rag_pipeline.answer(question)

    assert expected_doc in result.document_ids, result.document_ids
    assert_test(LLMTestCase(input=question, actual_output=result.text), [KeywordCoverageMetric(facts)])


def test_rag_answer_is_faithful_to_retrieved_passages(rag_pipeline, faithfulness_metric):
    """Faithfulness is judged against what search really returned, not a curated context."""
    result = rag_pipeline.answer("When are refunds paid out?")

    assert_test(
        LLMTestCase(input=result.question, actual_output=result.text, retrieval_context=result.contexts),
        [faithfulness_metric],
    )


def test_pipeline_abstains_without_calling_llm_when_nothing_relevant(semantic, settings):
    """Below the relevance floor, the pipeline returns the standard abstention and spends zero LLM calls."""
    spy = ScriptedChatbot(["this should never be returned"])
    pipeline = RagPipeline(semantic, spy, k=3, min_score=settings.semantic_min_score)

    result = pipeline.answer("recipe for sourdough bread")

    assert result.text == NO_ANSWER
    assert spy.calls == []
