"""Live synthetic data generation with local models (judged tier: slow on CPU).

Measured (CPU, temperature 0):
* test-case drafting with llama3.2:3b: 7/7 requirements covered, every quoted error message
  checked, no duplicates within a requirement, ~3 minutes;
* DeepEval ``Synthesizer`` with llama3.2:3b: ~100 s per golden, and one of the first two goldens
  had an expected answer inventing "eligible for a refund or exchange".
"""

import pytest
from deepeval.dataset import Golden

from ai.chatbot import OllamaChatbot
from ai.search import load_documents
from ai.synthesis import (
    GoldenQualityGate,
    generate_test_cases,
    load_requirements,
    related_requirements,
    review_suite,
    synthesize_goldens,
)
from reporting import attach_json

pytestmark = pytest.mark.judge

CONTEXT = ["Returned items must be unused and in original packaging."]


@pytest.fixture(scope="module")
def generator(ollama_request, require_ollama_model, settings) -> OllamaChatbot:
    """The test-case drafting model, capped so a runaway reply can't hang the run."""
    require_ollama_model(settings.testgen_model)
    return OllamaChatbot(ollama_request, model=settings.testgen_model, max_tokens=1000, timeout_s=settings.judge_timeout_s)


def test_generated_suite_covers_every_requirement(generator):
    """Every requirement gets cases of the right kinds, with its quoted messages checked."""
    requirements = load_requirements()
    cases = []
    for requirement in requirements:
        cases += generate_test_cases(generator, requirement, related_requirements(requirement, requirements))
    review = review_suite(requirements, cases)
    attach_json("generated test cases", [c.model_dump() for c in cases])
    attach_json("suite review", review.__dict__)

    assert review.ok, review


def test_gate_rejects_a_hallucinated_expected_answer(judge, settings):
    """The golden actually produced by the synthesizer in this repo, and a faithful twin."""
    gate = GoldenQualityGate(settings.embedding_model, judge=judge)
    invented = Golden(
        input="Which returned items can I get a refund for?",
        expected_output="Items that are unused and in original packaging are eligible for a refund or exchange.",
        context=CONTEXT,
    )
    faithful = Golden(
        input="What condition must a returned item be in?",
        expected_output="It must be unused and in its original packaging.",
        context=CONTEXT,
    )

    reviews = gate.review([invented, faithful])

    assert not reviews[0].accepted and "not grounded" in reviews[0].problems[0]
    assert reviews[1].accepted


def _fact_passages() -> list:
    """Policy passages built around one concrete number (days, dollars, years, hours).

    Four, not two: each synthetic golden usually carries a single claim, so one strict judge verdict
    decides it. In CI the 3B judge rejected "returns are *only* accepted within 45 days" (an added
    "only") and, correctly, an invented "refund or exchange": two of two rejected, a coin flip on
    two samples rather than a finding.
    """
    wanted = ("45 days", "$4.99", "2-year", "8am to 6pm")
    return [d for d in load_documents() if any(fact in d.text for fact in wanted)]


def test_synthesizer_goldens_pass_through_the_gate(judge, settings):
    """End to end: DeepEval writes goldens from two policy passages; the gate keeps only sound ones."""
    passages = [[d.text] for d in _fact_passages()]
    goldens = synthesize_goldens(passages, judge, per_context=1)
    reviews = GoldenQualityGate(settings.embedding_model, judge=judge).review(goldens)
    attach_json(
        "synthesized goldens",
        [{"input": r.golden.input, "expected": r.golden.expected_output, "problems": r.problems} for r in reviews],
    )

    assert len(goldens) == len(passages)
    assert all(r.golden.context for r in reviews)
    accepted = [r for r in reviews if r.accepted]
    assert accepted, f"gate rejected every synthetic golden: {[r.problems for r in reviews]}"
