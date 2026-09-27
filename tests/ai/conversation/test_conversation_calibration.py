"""Calibration of DeepEval's conversational metrics on known-good and known-bad conversations.

A judged metric is trusted only where it separates the two. Measured:

=======================  ==================  ==================
Metric                   llama3.2:3b         qwen2.5:7b
=======================  ==================  ==================
ConversationCompleteness good 1.0 / bad 0.4  (not needed)
RoleAdherence            see below           good 1.0 / bad 0.67
TurnRelevancy            good 1.0 / bad 1.0  good 1.0 / bad 0.33
KnowledgeRetention       good 0.67 / bad 0.67 good 1.0 / bad 1.0
=======================  ==================  ==================

RoleAdherence on the 3B judge scored good 0.67 / bad 0 locally but good 0.0 / bad 0.0 on GitHub
runners, and its reasons quote the *user's* line "what was my order number again?" as the
chatbot going out of character: it confuses the speakers, so the local pass was luck. The bad
conversation has one out-of-role reply in three (the poem), so 0.67 is the right score and the
7B judge gets both conversations right; a 0.8 threshold fails any single out-of-role reply.

So completeness gates on the default judge, role adherence and turn relevancy only on the
strong judge, and knowledge retention on neither: the rule-based ``RetentionProbeMetric``
covers memory instead.
"""

from ai.evaluators import MetricFactory


def scores(metric_factory, good, bad) -> tuple[float, float]:
    """Score the good and the bad conversation with fresh metric instances."""
    results = []
    for case in (good, bad):
        metric = metric_factory()
        metric.measure(case)
        results.append(metric.score)
    return tuple(results)


def test_default_judge_separates_complete_from_incomplete(judge, good_conversation, bad_conversation):
    """On the 3B judge the good conversation is complete and the bad one is not."""
    factory = MetricFactory(judge)

    good, bad = scores(lambda: factory.conversation_completeness(threshold=0.7), good_conversation, bad_conversation)

    assert good >= 0.7 > bad, (good, bad)


def test_role_adherence_needs_the_strong_judge(strong_metrics, good_conversation, bad_conversation):
    """The 7B judge scores the in-role conversation 1.0 and the one with a poem 2/3."""
    good, bad = scores(lambda: strong_metrics.role_adherence(threshold=0.8), good_conversation, bad_conversation)

    assert good >= 0.8 > bad, (good, bad)


def test_turn_relevancy_needs_the_strong_judge(strong_metrics, good_conversation, bad_conversation):
    """The 7B judge notices the off-topic poem that the 3B judge scored as relevant."""
    good, bad = scores(lambda: strong_metrics.turn_relevancy(threshold=0.7), good_conversation, bad_conversation)

    assert good >= 0.7 > bad, (good, bad)
