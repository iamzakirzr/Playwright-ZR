"""Evaluating from a DeepEval ``EvaluationDataset``: the dataset-driven style used in production.

Goldens hold inputs and expectations; the test fills in ``actual_output`` from
the live bot, turning each Golden into an ``LLMTestCase``. The dataset object
itself is checked offline, so a malformed golden fails fast before any model runs.
"""

import pytest
from deepeval import assert_test
from deepeval.test_case import LLMTestCase

from ai.datasets import adversarial_dataset, golden_dataset
from ai.evaluators import KeywordCoverageMetric

DATASET = golden_dataset()


def test_golden_dataset_is_well_formed():
    """Every golden has an input, an expected output, context and at least one required fact."""
    assert DATASET.goldens
    for golden in DATASET.goldens:
        assert golden.input and golden.expected_output and golden.context
        assert golden.additional_metadata["required_facts"]


def test_adversarial_dataset_covers_owasp_categories():
    """The adversarial goldens span at least five OWASP LLM Top-10 categories."""
    owasp = {g.additional_metadata["owasp"] for g in adversarial_dataset().goldens}
    assert len(owasp) >= 5, owasp


@pytest.mark.parametrize("golden", DATASET.goldens, ids=[g.additional_metadata["id"] for g in DATASET.goldens])
def test_live_answers_for_each_golden(ask, similarity_metric, golden):
    """Golden → live answer → LLMTestCase → similarity and required-fact metrics."""
    answer = ask(golden.input, golden.context).text
    test_case = LLMTestCase(
        input=golden.input, actual_output=answer, expected_output=golden.expected_output, context=golden.context
    )

    assert_test(test_case, [similarity_metric, KeywordCoverageMetric(golden.additional_metadata["required_facts"])])
