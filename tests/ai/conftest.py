"""AI-suite fixtures: chatbots, judges, metric factory, retrievers and RAG.

Dependency graph (every arrow is fixture injection)::

    ollama_request ─▶ ollama_models ─▶ chatbot ─▶ guarded_chatbot   (Ollama fixtures: root conftest.py)
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
from reporting import attach_llm_exchange


@pytest.fixture(scope="session", autouse=True)
def _deepeval_timeouts(settings):
    """Give CPU-bound judge calls enough time (DeepEval's default is about 90 s)."""
    os.environ.setdefault("DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE", str(settings.judge_timeout_s))


# --------------------------------------------------------------------------- #
# Chatbots
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def chatbot(ollama_request, require_ollama_model, settings) -> OllamaChatbot:
    """The raw chatbot under test (no guard rails)."""
    require_ollama_model(settings.chatbot_model)
    return OllamaChatbot(
        ollama_request,
        model=settings.chatbot_model,
        temperature=settings.chatbot_temperature,
        seed=settings.chatbot_seed,
        timeout_s=settings.chatbot_timeout_s,
        canary=settings.canary_token,
    )


@pytest.fixture(scope="session")
def moderator(ollama_request, require_ollama_model, settings) -> OllamaChatbot:
    """A separate chatbot instance that runs the input-moderation prompt."""
    require_ollama_model(settings.effective_moderator_model)
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
        response = cache[key]
        attach_llm_exchange(
            question,
            response.text,
            model=response.model,
            context=context,
            latency_ms=round(response.latency_ms),
            completion_tokens=response.completion_tokens,
        )
        return response

    return _ask


# --------------------------------------------------------------------------- #
# Judges and metrics
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def judge(require_ollama_model, settings):
    """DeepEval judge LLM for quality metrics."""
    from ai.evaluators import deepeval_judge

    require_ollama_model(settings.judge_model)
    return deepeval_judge(settings.judge_model, settings.ollama_host)


@pytest.fixture(scope="session")
def metrics(judge, settings):
    """:class:`MetricFactory` bound to the quality judge."""
    from ai.evaluators import MetricFactory

    return MetricFactory(judge, threshold=settings.quality_threshold)


@pytest.fixture(scope="session")
def strong_metrics(require_ollama_model, settings):
    """:class:`MetricFactory` bound to the stronger judge (opt-in: skips if not pulled).

    Used for metrics the default 3B judge failed to calibrate on: answer relevancy
    (scored an on-topic answer 0.25), correctness (flat 0.6 for right and wrong),
    hallucination (inverted), and the LLM-judged safety metrics.
    """
    from ai.evaluators import MetricFactory, deepeval_judge

    require_ollama_model(settings.strong_judge_model)
    return MetricFactory(deepeval_judge(settings.strong_judge_model, settings.ollama_host), threshold=settings.quality_threshold)


@pytest.fixture(scope="session")
def ragas_llm(require_ollama_model, settings):
    """Ragas-wrapped judge (opt-in: needs a model of 7B or more)."""
    from ai.evaluators import ragas_judge

    require_ollama_model(settings.ragas_judge_model)
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
