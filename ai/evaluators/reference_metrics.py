"""Traditional reference-based metrics (BLEU, ROUGE) through Hugging Face ``evaluate``.

These count overlapping words or n-grams between the output and a reference. They are fast,
deterministic and standard for summarisation and translation, **but they reward wording, not
meaning**: "You have 45 days after delivery to send an item back" scores ROUGE-L 0.32 and BLEU
0.08 against "Returns are accepted within 45 days of delivery", although it is correct.
``tests/ai/validation/test_reference_metrics.py`` proves this on every run.

Use them when the wording itself is the requirement (templated messages, extractive
summaries, regression against a previous model's output). For free-form LLM answers, prefer
semantic similarity and the judged metrics.

Metric scripts are downloaded from the Hugging Face Hub on first use and then cached.
"""

from __future__ import annotations

from functools import cache
from typing import Any

from deepeval.test_case import LLMTestCase

from ai.evaluators.base import DeterministicMetric


@cache
def load_hf_metric(name: str) -> Any:
    """Load (once per process) a metric from Hugging Face ``evaluate``, e.g. ``"rouge"``."""
    import evaluate

    return evaluate.load(name)


def rouge_scores(prediction: str, reference: str) -> dict[str, float]:
    """ROUGE-1, ROUGE-2 and ROUGE-L F-measures (0 to 1) for one prediction."""
    result = load_hf_metric("rouge").compute(predictions=[prediction], references=[reference])
    return {key: float(result[key]) for key in ("rouge1", "rouge2", "rougeL")}


def bleu_score(prediction: str, reference: str) -> float:
    """SacreBLEU score scaled to 0 to 1 (SacreBLEU reports 0 to 100)."""
    return float(load_hf_metric("sacrebleu").compute(predictions=[prediction], references=[[reference]])["score"]) / 100


class _ReferenceMetric(DeterministicMetric):
    """Shared plumbing: needs ``expected_output`` and compares ``actual_output`` with it."""

    def compare(self, prediction: str, reference: str) -> float:
        """Subclasses return the 0-1 score for one pair.

        (Not named ``score``: DeepEval stores each result in the instance attribute ``score``.)
        """
        raise NotImplementedError

    def evaluate(self, test_case: LLMTestCase) -> tuple[float, str]:
        """Score ``actual_output`` against ``expected_output``.

        Raises:
            ValueError: If the test case has no ``expected_output``.
        """
        if not test_case.expected_output:
            raise ValueError(f"{self.metric_name} needs expected_output on the test case")
        value = self.compare(test_case.actual_output, test_case.expected_output)
        return value, f"{self.metric_name}={value:.2f}"


class RougeMetric(_ReferenceMetric):
    """ROUGE F-measure (default ROUGE-L: longest common subsequence).

    Args:
        threshold: Minimum score to pass.
        variant: ``"rouge1"``, ``"rouge2"`` or ``"rougeL"``.
    """

    metric_name = "ROUGE"

    def __init__(self, threshold: float = 0.5, variant: str = "rougeL") -> None:
        """Create the RougeMetric; arguments are described in the class docstring."""
        super().__init__(pass_threshold=threshold)
        self.variant = variant
        self.metric_name = f"ROUGE ({variant})"

    def compare(self, prediction: str, reference: str) -> float:
        """The chosen ROUGE variant's F-measure."""
        return rouge_scores(prediction, reference)[self.variant]


class BleuMetric(_ReferenceMetric):
    """SacreBLEU (n-gram precision with a brevity penalty), scaled to 0 to 1.

    Args:
        threshold: Minimum score to pass.
    """

    metric_name = "BLEU"

    def __init__(self, threshold: float = 0.3) -> None:
        """Create the BleuMetric; arguments are described in the class docstring."""
        super().__init__(pass_threshold=threshold)

    def compare(self, prediction: str, reference: str) -> float:
        """SacreBLEU / 100."""
        return bleu_score(prediction, reference)
