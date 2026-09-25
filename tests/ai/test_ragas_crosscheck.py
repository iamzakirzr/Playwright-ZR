"""Ragas cross-check of faithfulness with an independent implementation.

Two frameworks agreeing is stronger evidence than one. Ragas' structured
prompts need a >= 7B judge, so this is opt-in: it skips unless
RAGAS_JUDGE_MODEL is pulled in Ollama.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest

from ai.datasets import load_golden

CASE = next(c for c in load_golden("cases") if c["id"] == "warranty")


@pytest.mark.ragas
def test_ragas_faithfulness_on_live_answer(ask, ragas_llm, settings):
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
