"""Base class for custom, deterministic DeepEval metrics.

DeepEval's ``BaseMetric`` needs several attributes and both sync and async
``measure`` methods. ``DeterministicMetric`` implements that boilerplate once
(**Template Method**). A subclass only writes :meth:`evaluate`, returning a
score in [0, 1] and a human-readable reason.

Deterministic metrics need no judge LLM: they are fast, free and never flaky.
Prefer them wherever a rule can express the requirement, and save LLM judges
for what needs understanding.
"""
from __future__ import annotations

from abc import abstractmethod

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase


class DeterministicMetric(BaseMetric):
    """Abstract rule-based metric.

    Args:
        threshold: Minimum score that counts as a pass.
        higher_is_better: Set False for "risk" metrics, where the score measures a
            failure and the test passes when ``score <= threshold``.
    """

    #: Display name shown in DeepEval reports. Subclasses override.
    metric_name: str = "Deterministic Metric"

    def __init__(self, threshold: float = 0.5, higher_is_better: bool = True) -> None:
        """Create the DeterministicMetric; arguments are described in the class docstring."""
        self.threshold = threshold
        self.higher_is_better = higher_is_better
        self.include_reason = True
        self.async_mode = False
        self.strict_mode = False
        self.evaluation_model = "rule-based"
        self.score: float | None = None
        self.reason: str | None = None
        self.success: bool | None = None
        self.error: str | None = None

    @abstractmethod
    def evaluate(self, test_case: LLMTestCase) -> tuple[float, str]:
        """Score one test case.

        Returns:
            ``(score, reason)``, where ``score`` is in [0, 1].
        """

    def measure(self, test_case: LLMTestCase, *args, **kwargs) -> float:
        """Run :meth:`evaluate`, then record score, reason and pass/fail on the instance."""
        score, reason = self.evaluate(test_case)
        self.score = round(float(score), 4)
        self.success = self.score >= self.threshold if self.higher_is_better else self.score <= self.threshold
        comparator = ">=" if self.higher_is_better else "<="
        self.reason = f"{reason} (score {self.score}, pass if {comparator} {self.threshold})"
        return self.score

    async def a_measure(self, test_case: LLMTestCase, *args, **kwargs) -> float:
        """Async entry point required by DeepEval; the work is CPU-only, so it just delegates."""
        return self.measure(test_case)

    def is_successful(self) -> bool:
        """True when the last :meth:`measure` passed its threshold."""
        return bool(self.success)

    @property
    def __name__(self) -> str:
        """Name DeepEval prints in its results table."""
        return self.metric_name
