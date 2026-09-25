"""Ragas cross-check of faithfulness with an independent implementation.

Two frameworks agreeing is stronger evidence than one. Ragas' structured
prompts need a judge of 7B or more, so this test is opt-in: it skips unless
RAGAS_JUDGE_MODEL has been pulled into Ollama.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest

from ai.datasets import golden_case

CASE = golden_case("warranty")


@pytest.mark.ragas
def test_ragas_faithfulness_on_live_answer(ask, ragas_llm, settings):
    """Ragas must agree with DeepEval that the live warranty answer is faithful."""
    from ragas import SingleTurnSample
    from ragas.metrics import Faithfulness

    answer = ask(CASE["question"], CASE["context"]).text
    sample = SingleTurnSample(user_input=CASE["question"], response=answer, retrieved_contexts=CASE["context"])

    # Playwright's sync API owns the main thread's event loop, so Ragas' coroutine
    # gets its own loop on a worker thread.
    metric = Faithfulness(llm=ragas_llm)
    with ThreadPoolExecutor(max_workers=1) as pool:
        score = pool.submit(asyncio.run, metric.single_turn_ascore(sample)).result()

    assert score >= settings.faithfulness_threshold, f"Ragas faithfulness={score:.2f} for answer {answer!r}"
