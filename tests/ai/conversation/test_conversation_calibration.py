"""Calibration of DeepEval's conversational metrics on known-good and known-bad conversations.

A judged metric is trusted only where it separates the two. Measured:

=======================  ==================  ==================
Metric                   llama3.2:3b         qwen2.5:7b
=======================  ==================  ==================
ConversationCompleteness good 1.0 / bad 0.4  (not needed)
RoleAdherence            good 0.67 / bad 0   (not needed)
TurnRelevancy            good 1.0 / bad 1.0  good 1.0 / bad 0.33
KnowledgeRetention       good 0.67 / bad 0.67 good 1.0 / bad 1.0
=======================  ==================  ==================

So completeness and role adherence gate on the default judge, turn relevancy only on the
strong judge, and knowledge retention on neither: the rule-based ``RetentionProbeMetric``
covers memory instead.
"""

import pytest

from ai.evaluators import MetricFactory


def scores(metric_factory, good, bad) -> tuple[float, float]:
    """Score the good and the bad conversation with fresh metric instances."""
    results = []
    for case in (good, bad):
        metric = metric_factory()
        metric.measure(case)
        results.append(metric.score)
    return tuple(results)


@pytest.mark.parametrize(
    ("name", "threshold"),
    [("conversation_completeness", 0.7), ("role_adherence", 0.5)],
)
def test_default_judge_separates_good_from_bad(judge, good_conversation, bad_conversation, name, threshold):
    """On the 3B judge the good conversation passes and the bad one fails."""
    factory = MetricFactory(judge)

    good, bad = scores(lambda: getattr(factory, name)(threshold=threshold), good_conversation, bad_conversation)

    assert good >= threshold > bad, (good, bad)


def test_turn_relevancy_needs_the_strong_judge(strong_metrics, good_conversation, bad_conversation):
    """The 7B judge notices the off-topic poem that the 3B judge scored as relevant."""
    good, bad = scores(lambda: strong_metrics.turn_relevancy(threshold=0.7), good_conversation, bad_conversation)

    assert good >= 0.7 > bad, (good, bad)
