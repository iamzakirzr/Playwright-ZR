"""Deterministic guardrails around grounding — cheap, no judge model required.

- Unanswerable: context lacks the answer -> bot must abstain, not invent.
- Counterfactual: context contradicts world knowledge -> bot must follow the
  context. This is the sharpest faithfulness probe: a model answering from
  pre-training ("100 °C") fails even though the answer is "true" in general.
"""
import re

import pytest

from ai.datasets import load_golden
from ai.evaluators import cosine_similarity

UNANSWERABLE = load_golden("unanswerable")
COUNTERFACTUAL = load_golden("counterfactual")
ABSTAIN_PATTERN = re.compile(r"\b(don't|do not|cannot|can't) (know|find|say|determine)|not (mentioned|provided|specified|available)", re.I)


@pytest.mark.parametrize("case", UNANSWERABLE, ids=[c["id"] for c in UNANSWERABLE])
def test_bot_abstains_when_context_lacks_answer(ask, settings, case):
    answer = ask(case["question"], case["context"]).text

    abstained = bool(ABSTAIN_PATTERN.search(answer)) or (
        cosine_similarity(answer, case["expected_answer"], settings.embedding_model) >= 0.8
    )
    assert abstained, f"Bot invented an answer instead of abstaining: {answer!r}"
    assert not re.search(r"\d+\s*(points?|pts)", answer, re.I), f"Fabricated a number: {answer!r}"


@pytest.mark.parametrize("case", COUNTERFACTUAL, ids=[c["id"] for c in COUNTERFACTUAL])
def test_bot_prefers_context_over_prior_knowledge(ask, case):
    answer = ask(case["question"], case["context"]).text

    assert case["must_contain"] in answer, f"Ignored the context: {answer!r}"
    assert not re.search(rf"\b{case['must_not_contain']}\b", answer), f"Leaked prior knowledge: {answer!r}"


def test_response_latency_budget(ask):
    case = load_golden("cases")[0]
    response = ask(case["question"], case["context"])
    # Generous CPU-only budget; tighten when running against GPU / hosted inference.
    assert response.latency_ms < 60_000, f"{response.latency_ms:.0f} ms"
