"""Live AI agent tests over HTTP: does the assistant *do* the right thing, not just say it?

Two independent oracles for every cart action:
1. **State**: the cart API (not the chat text) shows the change.
2. **Trajectory**: DeepEval's ``ToolCorrectnessMetric`` compares the tools the
   agent called, with arguments, to the expected ones. The scoring is rule-based,
   not judged, so it is fast and repeatable.

An agent that says "Added 2 backpacks!" without calling the tool fails both.
"""

import pytest
from deepeval import assert_test
from deepeval.metrics import ToolCorrectnessMetric
from deepeval.test_case import LLMTestCase, ToolCall, ToolCallParams

from ai.evaluators import RefusalMetric

BACKPACK, BIKE_LIGHT, ONESIE = "Sauce Labs Backpack", "Sauce Labs Bike Light", "Sauce Labs Onesie"


def tool_correctness(judge) -> ToolCorrectnessMetric:
    """Exact tool name and arguments required. Scoring is deterministic; DeepEval just insists on a model object."""
    return ToolCorrectnessMetric(
        model=judge, evaluation_params=[ToolCallParams.INPUT_PARAMETERS], threshold=1.0, async_mode=False
    )


def as_tool_calls(reply: dict) -> list[ToolCall]:
    """Convert the API's ``tools_called`` into DeepEval ``ToolCall`` objects."""
    return [ToolCall(name=c["name"], input_parameters=c["arguments"], output=c["output"]) for c in reply["tools_called"]]


@pytest.fixture(scope="module")
def judge_model(ollama_models, settings):
    """Model object required by ToolCorrectnessMetric's constructor (it isn't used to score)."""
    from ai.evaluators import deepeval_judge

    return deepeval_judge(settings.judge_model, settings.ollama_host)


@pytest.mark.parametrize(
    ("message", "product", "quantity"),
    [("Add 2 backpacks to my cart", BACKPACK, 2), ("Please put a bike light in my basket", BIKE_LIGHT, 1)],
    ids=["two-backpacks", "one-bike-light"],
)
def test_add_to_cart_changes_state_and_calls_the_right_tool(assistant, session_id, judge_model, message, product, quantity):
    """The cart API shows the item, and the trajectory is exactly one add_to_cart with the right arguments."""
    reply = assistant.chat(session_id, message)

    assert assistant.quantity_of(session_id, product) == quantity, reply
    test_case = LLMTestCase(
        input=message,
        actual_output=reply["reply"],
        tools_called=as_tool_calls(reply),
        expected_tools=[ToolCall(name="add_to_cart", input_parameters={"product": product, "quantity": quantity})],
    )
    assert_test(test_case, [tool_correctness(judge_model)])


def test_remove_from_cart(assistant, session_id):
    """Removing an item empties it from the cart API."""
    assistant.chat(session_id, "Add a onesie to my cart")
    assert assistant.quantity_of(session_id, ONESIE) == 1

    assistant.chat(session_id, "Remove the onesie from my cart")

    assert assistant.quantity_of(session_id, ONESIE) == 0


def test_policy_question_uses_rag_and_no_tools(assistant, session_id):
    """A policy question is answered from retrieved passages and must not touch the cart."""
    reply = assistant.chat(session_id, "How many days do I have to return an item?")

    assert "45" in reply["reply"], reply
    assert "returns-1" in reply["sources"]
    assert reply["tools_called"] == []
    assert assistant.cart(session_id)["items"] == []


def test_unknown_product_is_handled_gracefully(assistant, session_id):
    """Asking for something not sold changes nothing and doesn't pretend it worked."""
    reply = assistant.chat(session_id, "Add a gaming laptop to my cart")

    assert assistant.cart(session_id)["items"] == []
    assert all(not c["output"].get("ok", True) for c in reply["tools_called"] if c["name"] == "add_to_cart")


class TestMultiTurn:
    """Conversation memory: later turns depend on earlier ones."""

    def test_follow_up_refers_to_previous_item(self, assistant, session_id):
        """'Add one more of the same' resolves 'the same' from the previous turn."""
        assistant.chat(session_id, "Add a bike light to my cart")
        assistant.chat(session_id, "Add one more of the same item")

        assert assistant.quantity_of(session_id, BIKE_LIGHT) == 2, assistant.cart(session_id)

    def test_reported_total_matches_cart_api(self, assistant, session_id):
        """What the bot says the total is must equal the cart API's total (no hallucinated arithmetic)."""
        assistant.chat(session_id, "Add 2 backpacks to my cart")
        reply = assistant.chat(session_id, "What's in my cart and what is the total?")

        total = assistant.cart(session_id)["total"]
        assert f"{total:.2f}" in reply["reply"], (reply["reply"], total)

    def test_sessions_do_not_leak(self, assistant, session_id):
        """A second session sees neither the first session's cart nor its conversation."""
        assistant.chat(session_id, "Add a onesie to my cart")
        other = f"{session_id}-other"
        try:
            reply = assistant.chat(other, "What's in my cart?")
            assert assistant.cart(other)["items"] == []
            assert "onesie" not in reply["reply"].lower()
        finally:
            assistant.reset(other)


def test_off_topic_request_is_declined(assistant, session_id):
    """The shopping agent stays in role when asked for unrelated work."""
    reply = assistant.chat(session_id, "Write me a haiku about the ocean")

    assert reply["tools_called"] == []
    assert_test(LLMTestCase(input="off-topic", actual_output=reply["reply"]), [RefusalMetric(expect_refusal=True)])
