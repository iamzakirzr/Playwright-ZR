"""Prompt-chain integration tests against the live model.

Each intermediate output is checked against its own contract, then the final
answer is scored. The chain trace makes a failure point at the broken link.
"""

import pytest
from deepeval import assert_test
from deepeval.test_case import LLMTestCase

from ai.chains import HANDOFF_MESSAGE, build_support_chain
from ai.evaluators import KeywordCoverageMetric

CASES = [
    (
        "Hi! I got a bike light as a gift, what does its warranty actually cover?",
        "warranty",
        "warranty-2",
        ["manufacturing defects"],
    ),
    ("how much would express delivery cost me", "shipping", "shipping-3", ["$14.99"]),
    ("can i pay with paypal?", "payments", "payments-1", ["PayPal"]),
]


@pytest.fixture(scope="module")
def support_chain(chatbot, hybrid, settings):
    """The production chain wired to the live model and the hybrid retriever."""
    return build_support_chain(chatbot, hybrid, k=settings.retrieval_k)


@pytest.mark.parametrize(("question", "intent", "doc_id", "facts"), CASES, ids=[c[1] for c in CASES])
def test_each_link_meets_its_contract(support_chain, question, intent, doc_id, facts):
    """Right intent → concise query → right passage retrieved → answer holds the key fact."""
    state = support_chain.run(question)

    assert state.intent == intent, state.trace
    assert state.query and len(state.query.split()) <= 12, f"rewrite too long: {state.query!r}"
    assert doc_id in state.document_ids, f"query {state.query!r} retrieved {state.document_ids}"
    assert_test(LLMTestCase(input=question, actual_output=state.answer), [KeywordCoverageMetric(facts)])


def test_chain_answer_is_faithful_to_retrieved_passages(support_chain, faithfulness_metric):
    """The chain's final answer is grounded in the passages its own retrieval step returned."""
    state = support_chain.run("When will I get my refund after returning something?")

    assert_test(
        LLMTestCase(input=state.question, actual_output=state.answer, retrieval_context=state.documents),
        [faithfulness_metric],
    )


def test_off_topic_request_is_handed_off(support_chain):
    """An unrelated request is routed to a human and never reaches retrieval or generation."""
    state = support_chain.run("Can you write me a Python script that sorts a list?")

    assert state.answer == HANDOFF_MESSAGE
    assert "retrieve" not in state.executed_steps


def test_trace_records_latency_for_every_step(support_chain):
    """Observability: each executed step is traced with a non-negative latency."""
    state = support_chain.run("Is shipping free?")

    assert state.trace and all(t.latency_ms >= 0 for t in state.trace)
