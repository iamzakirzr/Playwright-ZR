"""AI-suite fixtures: chatbots, judges, metric factory, retrievers and RAG.

Dependency graph (every arrow is fixture injection)::

    ollama_request ─▶ ollama_models ─▶ chatbot ─▶ guarded_chatbot
                                   ├─▶ judge ─▶ metrics (MetricFactory)
                                   └─▶ strong_metrics (opt-in 7B judge)
    documents ─▶ bm25 / semantic ─▶ hybrid ─▶ rag_pipeline(chatbot)

Tests that need Ollama *skip* (never fail) when it or a model is missing,
so ``pytest -m "ai and not live"`` still runs the offline AI tests anywhere.
"""
from __future__ import annotations

import os

import pytest

from ai.chatbot import ChatResponse, GuardedChatbot, OllamaChatbot
from ai.search import BM25Retriever, HybridRetriever, RagPipeline, SemanticRetriever, load_corpus, load_documents


@pytest.fixture(scope="session", autouse=True)
def _deepeval_timeouts(settings):
    """Give CPU-bound judge calls enough time (DeepEval's default is about 90 s)."""
    os.environ.setdefault("DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE", str(settings.judge_timeout_s))


# --------------------------------------------------------------------------- #
# Ollama plumbing
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def ollama_request(playwright, settings):
    """Playwright request context pointed at the Ollama server."""
    ctx = playwright.request.new_context(base_url=settings.ollama_host)
    yield ctx
    ctx.dispose()


@pytest.fixture(scope="session")
def ollama_models(ollama_request) -> set[str]:
    """Names of pulled models; skips the test when Ollama is unreachable."""
    try:
        response = ollama_request.get("/api/tags", timeout=5_000)
        models = {m["name"] for m in response.json().get("models", [])} if response.ok else set()
    except Exception:  # noqa: BLE001 - any failure means "not available"
        models = set()
    if not models:
        pytest.skip("Ollama is not reachable; start `ollama serve` to run live AI tests")
    return models


def require_model(models: set[str], name: str) -> None:
    """Skip the current test unless ``name`` has been pulled into Ollama."""
    if name not in models:
        pytest.skip(f"Model '{name}' not pulled; run `ollama pull {name}`")


# --------------------------------------------------------------------------- #
# Chatbots
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def chatbot(ollama_request, ollama_models, settings) -> OllamaChatbot:
    """The raw chatbot under test (no guard rails)."""
    require_model(ollama_models, settings.chatbot_model)
    return OllamaChatbot(
        ollama_request,
        model=settings.chatbot_model,
        temperature=settings.chatbot_temperature,
        seed=settings.chatbot_seed,
        timeout_s=settings.chatbot_timeout_s,
        canary=settings.canary_token,
    )


@pytest.fixture(scope="session")
def moderator(ollama_request, ollama_models, settings) -> OllamaChatbot:
    """A separate chatbot instance that runs the input-moderation prompt."""
    require_model(ollama_models, settings.effective_moderator_model)
    return OllamaChatbot(ollama_request, model=settings.effective_moderator_model, timeout_s=settings.chatbot_timeout_s)


@pytest.fixture(scope="session")
def guarded_chatbot(chatbot, moderator) -> GuardedChatbot:
    """The production configuration: raw bot plus signature filter, moderator and output redaction."""
    return GuardedChatbot(chatbot, moderator=moderator)


@pytest.fixture(scope="session")
def ask(chatbot):
    """Memoised ``chatbot.ask``: several metrics score one live answer, not several divergent ones."""
    cache: dict[tuple, ChatResponse] = {}

    def _ask(question: str, context: list[str] | None = None) -> ChatResponse:
        """Return the cached answer for (question, context), calling the bot on first use."""
        key = (question, tuple(context or ()))
        if key not in cache:
            cache[key] = chatbot.ask(question, context)
        return cache[key]

    return _ask


# --------------------------------------------------------------------------- #
# Judges and metrics
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def judge(ollama_models, settings):
    """DeepEval judge LLM for quality metrics."""
    from ai.evaluators import deepeval_judge

    require_model(ollama_models, settings.judge_model)
    return deepeval_judge(settings.judge_model, settings.ollama_host)


@pytest.fixture(scope="session")
def metrics(judge, settings):
    """:class:`MetricFactory` bound to the quality judge."""
    from ai.evaluators import MetricFactory

    return MetricFactory(judge, threshold=settings.quality_threshold)


@pytest.fixture(scope="session")
def strong_metrics(ollama_models, settings):
    """:class:`MetricFactory` bound to the stronger judge (opt-in: skips if not pulled).

    Used for metrics the default 3B judge failed to calibrate on: answer relevancy
    (scored an on-topic answer 0.25), correctness (flat 0.6 for right and wrong),
    hallucination (inverted), and the LLM-judged safety metrics.
    """
    from ai.evaluators import MetricFactory, deepeval_judge

    require_model(ollama_models, settings.strong_judge_model)
    return MetricFactory(deepeval_judge(settings.strong_judge_model, settings.ollama_host), threshold=settings.quality_threshold)


@pytest.fixture(scope="session")
def ragas_llm(ollama_models, settings):
    """Ragas-wrapped judge (opt-in: needs a model of 7B or more)."""
    from ai.evaluators import ragas_judge

    require_model(ollama_models, settings.ragas_judge_model)
    return ragas_judge(settings.ragas_judge_model, settings.ollama_host)


@pytest.fixture
def similarity_metric(settings):
    """Fresh embedding-similarity metric at the configured threshold."""
    from ai.evaluators import SemanticSimilarityMetric

    return SemanticSimilarityMetric(settings.embedding_model, threshold=settings.similarity_threshold)


@pytest.fixture
def faithfulness_metric(metrics, settings):
    """Fresh DeepEval faithfulness metric at the configured threshold."""
    return metrics.faithfulness(settings.faithfulness_threshold)


# --------------------------------------------------------------------------- #
# Search / RAG
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def corpus() -> dict:
    """Raw corpus JSON: documents, labelled queries, robustness and off-domain probes."""
    return load_corpus()


@pytest.fixture(scope="session")
def documents():
    """The knowledge-base documents."""
    return load_documents()


@pytest.fixture(scope="session")
def bm25(documents) -> BM25Retriever:
    """Keyword retriever."""
    return BM25Retriever(documents)


@pytest.fixture(scope="session")
def semantic(documents, settings) -> SemanticRetriever:
    """Embedding retriever."""
    return SemanticRetriever(documents, settings.embedding_model)


@pytest.fixture(scope="session")
def hybrid(bm25, semantic) -> HybridRetriever:
    """Reciprocal-rank fusion of BM25 and semantic retrieval (the production retriever)."""
    return HybridRetriever([bm25, semantic])


@pytest.fixture(scope="session")
def retrievers(bm25, semantic, hybrid) -> dict:
    """All retrieval strategies by name, for parametrised comparisons."""
    return {r.name: r for r in (bm25, semantic, hybrid)}


@pytest.fixture(scope="session")
def rag_pipeline(hybrid, chatbot, settings) -> RagPipeline:
    """Live RAG: hybrid search plus the chatbot."""
    return RagPipeline(hybrid, chatbot, k=settings.retrieval_k)
