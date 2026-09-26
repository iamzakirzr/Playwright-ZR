"""Offline calibration of the deterministic metrics.

A metric is a test oracle. If the oracle is wrong, every test built on it is
wrong. Each metric gets one known-good and one known-bad input.
"""

import pytest
from deepeval.test_case import LLMTestCase
from pydantic import BaseModel

from ai.evaluators import (
    CanaryLeakageMetric,
    JsonSchemaMetric,
    KeywordCoverageMetric,
    RefusalMetric,
    RegexPIIMetric,
    SemanticSimilarityMetric,
    ToxicityClassifierMetric,
    WordLimitMetric,
)


def case(output: str, expected: str | None = None) -> LLMTestCase:
    """Minimal DeepEval test case around ``output``."""
    return LLMTestCase(input="q", actual_output=output, expected_output=expected)


class Item(BaseModel):
    """Toy schema for the JSON metric."""

    name: str
    qty: int


class TestJsonSchemaMetric:
    """JSON parse and schema validation."""

    def test_valid_json_passes(self):
        """Well-formed JSON matching the schema scores 1."""
        m = JsonSchemaMetric(Item)
        m.measure(case('{"name": "light", "qty": 2}'))
        assert m.is_successful(), m.reason

    @pytest.mark.parametrize(
        ("bad", "reason"),
        [
            ("not json", "invalid JSON"),
            ('{"name": "light"}', "schema violation"),
            ('{"name": 1, "qty": "x"}', "schema violation"),
        ],
    )
    def test_invalid_json_fails_with_reason(self, bad, reason):
        """Unparseable or off-schema output scores 0 with a useful reason."""
        m = JsonSchemaMetric(Item)
        m.measure(case(bad))
        assert not m.is_successful()
        assert reason in m.reason


def test_word_limit_metric():
    """Counts words and enforces the ceiling."""
    assert WordLimitMetric(3).measure(case("one two three")) == 1.0
    assert WordLimitMetric(3).measure(case("one two three four")) == 0.0


def test_keyword_coverage_metric_reports_missing_facts():
    """Partial coverage scores proportionally and names what is missing."""
    m = KeywordCoverageMetric(["$4.99", "$75", "$14.99"], threshold=1.0)
    m.measure(case("Orders of $75 or more ship free."))
    assert m.score == pytest.approx(1 / 3, abs=1e-3)
    assert "$4.99" in m.reason and not m.is_successful()


def test_regex_pii_metric():
    """Detects PII categories and honours an allow-list."""
    assert RegexPIIMetric().measure(case("SSN 123-45-6789")) > 0
    assert RegexPIIMetric(allowed=("help@sauce.example",)).measure(case("Email help@sauce.example")) == 0.0


def test_similarity_metric_requires_reference(settings):
    """Similarity without an expected_output is a usage error, not a silent zero."""
    with pytest.raises(ValueError, match="expected_output"):
        SemanticSimilarityMetric(settings.embedding_model).measure(case("anything"))


ALL_CUSTOM_METRICS = [
    lambda s: SemanticSimilarityMetric(s.embedding_model, threshold=0.42),
    lambda s: KeywordCoverageMetric(["a", "b"], threshold=0.5),
    lambda s: JsonSchemaMetric(Item),
    lambda s: WordLimitMetric(7),
    lambda s: RegexPIIMetric(allowed=("x@y.z",)),
    lambda s: RefusalMetric(expect_refusal=False),
    lambda s: CanaryLeakageMetric("CANARY"),
    lambda s: ToxicityClassifierMetric(threshold=0.3),
]


@pytest.mark.parametrize(
    "build", ALL_CUSTOM_METRICS, ids=["similarity", "keywords", "json", "words", "pii", "no-refusal", "canary", "toxicity"]
)
def test_metric_survives_deepeval_cloning(settings, build):
    """``assert_test`` clones metrics through their constructors; every custom metric must round-trip.

    Regression: a base-class ``__init__`` parameter named like an attribute made
    DeepEval pass unexpected keyword arguments and crash every ``assert_test``.
    """
    from deepeval.metrics.utils import copy_metrics

    original = build(settings)
    (clone,) = copy_metrics([original])

    assert type(clone) is type(original)
    assert clone.threshold == original.threshold
    assert clone._lower_is_better == original._lower_is_better
