"""AI-suite fixtures: live chatbot, judge model, metrics, and an answer cache.

Every AI test skips (not fails) when Ollama or a required model is missing,
so the UI/API/SQL suites stay runnable on any machine.
"""
from __future__ import annotations

import pytest

from ai.chatbot import ChatResponse, OllamaChatbot


def _pulled_models(api_request_ctx) -> set[str]:
    try:
        response = api_request_ctx.get("/api/tags", timeout=5_000)
        return {m["name"] for m in response.json().get("models", [])} if response.ok else set()
    except Exception:
        return set()


@pytest.fixture(scope="session")
def ollama_request(playwright, settings):
    ctx = playwright.request.new_context(base_url=settings.ollama_host)
    yield ctx
    ctx.dispose()


@pytest.fixture(scope="session")
def ollama_models(ollama_request) -> set[str]:
    models = _pulled_models(ollama_request)
    if not models:
        pytest.skip("Ollama is not reachable — start `ollama serve` to run AI tests")
    return models


def _require(models: set[str], name: str) -> None:
    if name not in models:
        pytest.skip(f"Model '{name}' not pulled — run `ollama pull {name}`")


@pytest.fixture(scope="session")
def chatbot(ollama_request, ollama_models, settings) -> OllamaChatbot:
    _require(ollama_models, settings.chatbot_model)
    return OllamaChatbot(
        ollama_request,
        model=settings.chatbot_model,
        temperature=settings.chatbot_temperature,
        seed=settings.chatbot_seed,
        timeout_s=settings.chatbot_timeout_s,
    )


@pytest.fixture(scope="session")
def ask(chatbot):
    """Memoised `chatbot.ask` — similarity and faithfulness tests score the
    same live answer instead of paying for (and diverging on) a second call."""
    cache: dict[tuple, ChatResponse] = {}

    def _ask(question: str, context: list[str] | None = None) -> ChatResponse:
        key = (question, tuple(context or ()))
        if key not in cache:
            cache[key] = chatbot.ask(question, context)
        return cache[key]

    return _ask


@pytest.fixture(scope="session")
def judge(ollama_models, settings):
    from ai.evaluators import deepeval_judge

    _require(ollama_models, settings.judge_model)
    return deepeval_judge(settings.judge_model, settings.ollama_host)


@pytest.fixture(scope="session")
def ragas_llm(ollama_models, settings):
    from ai.evaluators import ragas_judge

    _require(ollama_models, settings.ragas_judge_model)
    return ragas_judge(settings.ragas_judge_model, settings.ollama_host)


@pytest.fixture
def similarity_metric(settings):
    from ai.evaluators import SemanticSimilarityMetric

    return SemanticSimilarityMetric(settings.embedding_model, threshold=settings.similarity_threshold)


@pytest.fixture
def faithfulness_metric(judge, settings):
    from deepeval.metrics import FaithfulnessMetric

    return FaithfulnessMetric(
        threshold=settings.faithfulness_threshold,
        model=judge,
        async_mode=False,
        include_reason=True,
    )
