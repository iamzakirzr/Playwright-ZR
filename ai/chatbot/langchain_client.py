"""A LangChain application under test, behind the same ``ChatbotClient`` interface.

Teams often ship RAG apps built with LangChain. This adapter *is* such an app, written in LCEL
(LangChain Expression Language)::

    retrieve  ->  build messages  ->  chat model  ->  AIMessage

and, because it is a :class:`ChatbotClient`, every metric and test in this repo runs against
it unchanged, so a LangChain app can be compared with the plain Ollama client on the same
golden set.

Design choices worth copying:

* **The prompt comes from the prompt registry**, rendered with ``string.Template``. LangChain's
  ``{placeholder}`` templates would re-interpret braces in user input; the registry's tests prove
  user text is inserted literally.
* **The model is injected** (any LangChain ``Runnable``), so unit tests replace it with a
  ``RunnableLambda`` that records exactly what the chain sent, with no model at all.
* **The retrieved context is kept** on ``last_context`` so faithfulness can be judged against
  what the chain actually used.
"""

from __future__ import annotations

import time
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import Runnable, RunnableLambda

from ai.chatbot.base import ChatbotClient, ChatResponse
from ai.search.base import Retriever


class LangChainChatbot(ChatbotClient):
    """RAG chatbot implemented as an LCEL chain.

    Args:
        llm: Chat model (e.g. ``ChatOllama``) or any Runnable taking messages and returning an ``AIMessage``.
        retriever: Used by :meth:`ask` when no context is passed; None means answer without context.
        k: Passages to retrieve.
        model_name: Name reported in :class:`ChatResponse`.
        **kwargs: Forwarded to :class:`ChatbotClient` (prompt templates, canary).
    """

    def __init__(
        self, llm: Runnable, retriever: Retriever | None = None, k: int = 3, model_name: str = "langchain", **kwargs
    ) -> None:
        """Create the LangChainChatbot; arguments are described in the class docstring."""
        super().__init__(**kwargs)
        self.llm = llm
        self.retriever = retriever
        self.k = k
        self.model_name = model_name
        self.last_context: list[str] = []
        #: The RAG pipeline as one LCEL runnable: {"question", "context"} -> AIMessage.
        self.rag_chain: Runnable = RunnableLambda(self._retrieve) | RunnableLambda(self._messages) | self.llm

    @classmethod
    def from_ollama(
        cls,
        model: str,
        host: str,
        retriever: Retriever | None = None,
        temperature: float = 0.0,
        seed: int = 42,
        **kwargs: Any,
    ) -> LangChainChatbot:
        """Build the app on a local Ollama model through ``langchain-ollama``."""
        from langchain_ollama import ChatOllama

        llm = ChatOllama(model=model, base_url=host, temperature=temperature, seed=seed)
        return cls(llm, retriever=retriever, model_name=model, **kwargs)

    # -- chain steps -----------------------------------------------------------
    def _retrieve(self, inputs: dict) -> dict:
        """Keep caller-supplied context (even ``[]``: "answer without context"); for None, retrieve ``k`` passages."""
        context = inputs.get("context")
        if context is None and self.retriever is not None:
            context = [hit.document.text for hit in self.retriever.search(inputs["question"], k=self.k)]
        self.last_context = list(context or [])
        return {**inputs, "context": self.last_context}

    def _messages(self, inputs: dict) -> list[BaseMessage]:
        """Render the registry prompt (grounded when there is context) into chat messages."""
        if inputs["context"]:
            prompt = self.grounded_prompt.render(
                context="\n".join(f"- {c}" for c in inputs["context"]), canary=self.canary, question=inputs["question"]
            )
        else:
            prompt = self.open_prompt.render(canary=self.canary, question=inputs["question"])
        return [SystemMessage(prompt.system), HumanMessage(prompt.user)]

    # -- ChatbotClient ---------------------------------------------------------
    def is_available(self) -> bool:
        """True if the model answers a trivial prompt."""
        try:
            self.llm.invoke([HumanMessage("ping")])
        except Exception:  # noqa: BLE001 - any failure means "not available"
            return False
        return True

    def ask(self, question: str, context: list[str] | None = None) -> ChatResponse:
        """Run the RAG chain; with ``context`` the retriever is skipped (like the other clients)."""
        return self._timed(lambda: self.rag_chain.invoke({"question": question, "context": context}))

    def complete(self, system: str, user: str, *, json_mode: bool = False) -> ChatResponse:
        """One system + user exchange straight to the model (used by prompt and chain tests)."""
        # format="json" is passed per call, not via .bind(): binding a RunnableRetry rebuilds it with
        # default retry settings. Only chat models (also wrapped ones) get it; test doubles don't.
        kwargs = {"format": "json"} if json_mode and _is_chat_model(self.llm) else {}
        return self._timed(lambda: self.llm.invoke([SystemMessage(system), HumanMessage(user)], **kwargs))

    def _timed(self, call) -> ChatResponse:
        """Invoke ``call`` and wrap its ``AIMessage`` (or string) with latency and token counts."""
        started = time.perf_counter()
        message = call()
        latency_ms = (time.perf_counter() - started) * 1000
        # AIMessage.text keeps only text blocks when content is a list of blocks.
        text = str(message.text) if isinstance(message, AIMessage) else str(message)
        usage = getattr(message, "usage_metadata", None) or {}
        return ChatResponse(
            text=text.strip(),
            model=self.model_name,
            latency_ms=latency_ms,
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
        )


def _is_chat_model(runnable: Runnable) -> bool:
    """True for a chat model, also when wrapped by ``.bind()`` or ``.with_retry()`` (they expose ``.bound``)."""
    while not isinstance(runnable, BaseChatModel):
        runnable = getattr(runnable, "bound", None)
        if runnable is None:
            return False
    return True
