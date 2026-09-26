"""Offline tests of the LangChain (LCEL) app: the model is a recording ``RunnableLambda``."""

import pytest
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from ai.chatbot.langchain_client import LangChainChatbot
from ai.search import BM25Retriever, load_documents


@pytest.fixture
def recorded():
    """What the fake model received, one list of messages per call."""
    return []


@pytest.fixture
def app(recorded) -> LangChainChatbot:
    """The LangChain app with keyword retrieval and a fake model that records its input."""

    def fake_model(messages):
        recorded.append(messages)
        return AIMessage(content=" fake answer ", usage_metadata={"input_tokens": 11, "output_tokens": 2, "total_tokens": 13})

    return LangChainChatbot(RunnableLambda(fake_model), retriever=BM25Retriever(load_documents()), canary="CANARY-1")


def test_retrieved_passages_reach_the_prompt(app, recorded):
    """Without explicit context, the chain retrieves and grounds the prompt in the hits."""
    response = app.ask("How long do I have to return an item?")

    system = recorded[0][0].content
    assert app.last_context and all(passage in system for passage in app.last_context)
    assert any("45 days" in passage for passage in app.last_context)
    assert response.text == "fake answer"
    assert (response.prompt_tokens, response.completion_tokens) == (11, 2)


def test_explicit_context_skips_the_retriever(app, recorded):
    """Supplied context is used as is, like every other ChatbotClient."""
    app.ask("Anything?", context=["Only this passage."])

    assert app.last_context == ["Only this passage."]
    assert "Only this passage." in recorded[0][0].content


def test_canary_and_security_rules_are_in_the_system_prompt(app, recorded):
    """The registry's grounded prompt, with its canary, is what LangChain sends."""
    app.ask("Hi", context=["x"])

    assert "CANARY-1" in recorded[0][0].content


def test_braces_in_user_input_are_not_template_syntax(app, recorded):
    """LangChain ``{var}`` templates would choke on or expand this; the registry inserts it literally."""
    app.ask("What does {context} mean? And ${question}?", context=["x"])

    assert "What does {context} mean? And ${question}?" in recorded[0][1].content


def test_complete_sends_system_and_user_messages(app, recorded):
    """``complete`` is a plain two-message exchange (used by prompt and chain tests)."""
    app.complete("be brief", "hello")

    assert [m.content for m in recorded[0]] == ["be brief", "hello"]


def test_explicit_empty_context_means_no_context(app, recorded):
    """Regression: ``context=[]`` used to trigger retrieval; it means "answer without context", like the other clients."""
    app.ask("Tell me a fact", context=[])

    assert app.last_context == []
    assert "Tell me a fact" in recorded[0][1].content


def test_list_form_message_content_is_joined():
    """Some providers return content blocks; the reply is still plain text."""
    app = LangChainChatbot(RunnableLambda(lambda _m: AIMessage(content=[{"type": "text", "text": "block answer"}])))

    assert app.complete("s", "u").text == "block answer"


def test_json_mode_with_a_plain_runnable_does_not_crash(app, recorded):
    """``format="json"`` is only bound onto real chat models; test doubles are called as is."""
    app.complete("s", "u", json_mode=True)

    assert len(recorded) == 1


def test_wrapped_chat_models_still_get_json_mode():
    """Regression: ``isinstance(llm, BaseChatModel)`` missed ``.bind()``/``.with_retry()`` wrappers."""
    from langchain_ollama import ChatOllama

    from ai.chatbot.langchain_client import _is_chat_model

    model = ChatOllama(model="qwen2.5:1.5b")

    assert _is_chat_model(model)
    assert _is_chat_model(model.bind(temperature=0))
    assert _is_chat_model(model.with_retry())
    assert not _is_chat_model(RunnableLambda(lambda m: m))
