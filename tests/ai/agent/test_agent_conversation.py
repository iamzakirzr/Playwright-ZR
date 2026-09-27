"""Multi-turn evaluation of the shopping agent with DeepEval's conversational metrics.

One realistic conversation (add, policy question, remove, check) is scored three ways:
1. **State**: the cart API shows the net result (never trust the chat text alone).
2. **Rule-based memory**: the last reply states the remaining quantity (``RetentionProbeMetric``).
3. **Judged**: conversation completeness on the default 3B judge, and role adherence on the
   7B judge, each where it passed calibration (see ``tests/ai/conversation``).
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
    """Run the scripted conversation once in a fresh session; yield (session id, test case, transcript).

    The transcript keeps every reply *with its tool calls*, so a failure shows what the agent did,
    not only the final state (small models behave differently across CPUs).
    """
    session = "conv-" + str(id(assistant))
    transcript: list[dict] = []

    def send(message: str) -> str:
        reply = assistant.chat(session, message)
        transcript.append({"user": message, "reply": reply["reply"], "tools": reply["tools_called"]})
        return reply["reply"]

    try:
        case = run_conversation(send, USER_TURNS, chatbot_role=ROLE)
        attach_json("conversation", transcript)
        yield session, case, transcript
    finally:
        assistant.reset(session)


def trajectory(transcript: list[dict]) -> str:
    """Readable per-turn summary for assertion messages."""
    return "\n".join(
        f"  {t['user']!r} -> tools={[(c['name'], c['arguments'], c['output'].get('ok')) for c in t['tools']]} reply={t['reply'][:80]!r}"
        for t in transcript
    )


def test_net_cart_state_after_the_conversation(assistant, conversation):
    """Add 2, remove 1: exactly one backpack left."""
    session, _, transcript = conversation

    assert assistant.quantity_of(session, BACKPACK) == 1, "\n" + trajectory(transcript)


def test_last_reply_states_the_remaining_quantity(conversation):
    """The final answer says one backpack is left (rule-based, no judge)."""
    _, case, transcript = conversation
    one = ("1 x", "1 sauce", "one sauce", "one backpack", "1 backpack")
    probe = RetentionProbeMetric([one, "backpack"])

    probe.measure(case)

    assert probe.is_successful(), f"{probe.reason}\n{trajectory(transcript)}"


def test_conversation_is_complete(conversation, judge):
    """Every user goal met, judged by the 3B judge (calibrated for completeness)."""
    _, case, _transcript = conversation

    assert_test(case, [MetricFactory(judge).conversation_completeness(threshold=0.7)])


def test_every_reply_stays_in_role(conversation, strong_metrics):
    """No reply leaves the shopping-assistant role; needs the 7B judge (the 3B one confuses speakers)."""
    _, case, _transcript = conversation

    assert_test(case, [strong_metrics.role_adherence(threshold=0.8)])
