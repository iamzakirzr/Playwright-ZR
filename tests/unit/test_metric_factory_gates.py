"""Factory must not offer uncalibrated judged metrics as gates."""

from __future__ import annotations

import pytest

from ai.evaluators.factory import MetricFactory


class _DummyJudge:
    """Minimal stand-in; knowledge_retention fails before the judge is used."""

    def generate(self, *args, **kwargs):  # pragma: no cover - never called
        raise AssertionError("judge must not be called")


def test_knowledge_retention_is_disabled():
    """DeepEval KnowledgeRetentionMetric failed calibration; the factory refuses to build it."""
    factory = MetricFactory(_DummyJudge())

    with pytest.raises(RuntimeError, match="RetentionProbeMetric"):
        factory.knowledge_retention()
