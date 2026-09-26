"""Offline tests for the conversation driver and the rule-based retention probe."""

from deepeval import assert_test

from ai.evaluators import RetentionProbeMetric, run_conversation


def test_run_conversation_records_both_sides_in_order():
    """Each user message is sent in order and paired with the reply it got."""
    sent = []

    def echo(message):
        sent.append(message)
        return f"re: {message}"

    case = run_conversation(echo, ["one", "two"], chatbot_role="helper")

    assert sent == ["one", "two"]
    assert [(t.role, t.content) for t in case.turns] == [
        ("user", "one"),
        ("assistant", "re: one"),
        ("user", "two"),
        ("assistant", "re: two"),
    ]
    assert case.chatbot_role == "helper"


def test_retention_probe_passes_when_facts_are_repeated(good_conversation):
    """The last reply of the good conversation states the order number."""
    assert_test(good_conversation, [RetentionProbeMetric(["4471"])])


def test_retention_probe_fails_when_the_bot_re_asks(bad_conversation):
    """The forgetful bot asks for the number instead of stating it."""
    metric = RetentionProbeMetric(["4471"])

    metric.measure(bad_conversation)

    assert metric.score == 0.0 and not metric.is_successful()
    assert "4471" in metric.reason


def test_retention_probe_partial_score(good_conversation):
    """Score is the share of facts found; the threshold decides pass/fail."""
    metric = RetentionProbeMetric(["4471", "Priya"], threshold=0.5)

    metric.measure(good_conversation)

    assert metric.score == 0.5 and metric.is_successful()


def test_retention_probe_can_target_an_earlier_turn(good_conversation):
    """``turn=0`` checks the first reply (which greets Priya by name)."""
    metric = RetentionProbeMetric(["Priya"], turn=0)

    metric.measure(good_conversation)

    assert metric.is_successful()
