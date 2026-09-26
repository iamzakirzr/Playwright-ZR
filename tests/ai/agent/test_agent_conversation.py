"""Multi-turn evaluation of the shopping agent with DeepEval's conversational metrics.

One realistic conversation (add, policy question, remove, check) is scored three ways:
1. **State**: the cart API shows the net result (never trust the chat text alone).
2. **Rule-based memory**: the last reply states the remaining quantity (``RetentionProbeMetric``).
3. **Judged**: conversation completeness and role adherence, the two conversational metrics
   that passed calibration on the default 3B judge (see ``ai/evaluators/factory.py``).
"""

import pytest
from deepeval import assert_test

from ai.evaluators import MetricFactory, RetentionProbeMetric, run_conversation
from reporting import attach_json

BACKPACK = "Sauce Labs Backpack"
ROLE = "The Sauce Demo Store shopping assistant: manages the user's cart and answers store policy questions."
USER_TURNS = [
    "Please add 2 backpacks to my cart",
    "How many days do I have to return an item?",
    "Remove one backpack",
    "What's in my cart now?",
]


@pytest.fixture(scope="module")
def conversation(assistant):
    """Run the scripted conversation once in a fresh session; yield (session id, test case)."""
    session = "conv-" + str(id(assistant))
    try:
        case = run_conversation(lambda m: assistant.chat(session, m)["reply"], USER_TURNS, chatbot_role=ROLE)
        attach_json("conversation", [{"role": t.role, "content": t.content} for t in case.turns])
        yield session, case
    finally:
        assistant.reset(session)


def test_net_cart_state_after_the_conversation(assistant, conversation):
    """Add 2, remove 1: exactly one backpack left."""
    session, _ = conversation

    assert assistant.quantity_of(session, BACKPACK) == 1


def test_last_reply_states_the_remaining_quantity(conversation):
    """The final answer says one backpack is left (rule-based, no judge)."""
    _, case = conversation
    one = ("1 x", "1 sauce", "one sauce", "one backpack", "1 backpack")

    assert_test(case, [RetentionProbeMetric([one, "backpack"])])


def test_conversation_is_complete_and_in_role(conversation, judge, settings):
    """Every user goal met, every turn in role, judged by the calibrated 3B judge."""
    _, case = conversation
    factory = MetricFactory(judge)

    assert_test(case, [factory.conversation_completeness(threshold=0.7), factory.role_adherence(threshold=0.5)])
