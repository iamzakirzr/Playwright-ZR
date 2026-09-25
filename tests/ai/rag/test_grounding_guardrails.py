"""Deterministic grounding guard rails: cheap, and no judge model required.

- Unanswerable: the context lacks the answer, so the bot must abstain, not invent one.
- Counterfactual: the context contradicts world knowledge, so the bot must follow the
  context. This is the sharpest faithfulness probe: a model answering from
  pre-training ("100 °C") fails even though that answer is "true" in general.
"""
import re

import pytest
from deepeval import assert_test
from deepeval.test_case import LLMTestCase

from ai.datasets import load_golden
from ai.evaluators import RefusalMetric

UNANSWERABLE = load_golden("unanswerable")
COUNTERFACTUAL = load_golden("counterfactual")


@pytest.mark.parametrize("case", UNANSWERABLE, ids=[c["id"] for c in UNANSWERABLE])
def test_bot_abstains_when_context_lacks_answer(ask, case):
    """With no answer in the context, the bot must say it doesn't know and invent no numbers."""
    answer = ask(case["question"], case["context"]).text

    assert_test(LLMTestCase(input=case["question"], actual_output=answer), [RefusalMetric(expect_refusal=True)])
    assert not re.search(r"\d+\s*(points?|pts)", answer, re.I), f"Fabricated a number: {answer!r}"


@pytest.mark.parametrize("case", COUNTERFACTUAL, ids=[c["id"] for c in COUNTERFACTUAL])
def test_bot_prefers_context_over_prior_knowledge(ask, case):
    """When the context contradicts common knowledge, the context wins."""
    answer = ask(case["question"], case["context"]).text

    assert case["must_contain"] in answer, f"Ignored the context: {answer!r}"
    assert not re.search(rf"\b{case['must_not_contain']}\b", answer), f"Leaked prior knowledge: {answer!r}"
