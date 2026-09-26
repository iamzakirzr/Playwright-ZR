"""A four-step customer-support chain: classify → rewrite → retrieve → answer.

question ─▶ IntentStep ─▶ (out_of_scope? ─▶ HandoffStep, stop)
                │
                ▼
          RewriteStep ─▶ RetrieveStep ─▶ AnswerStep ─▶ answer
"""

from __future__ import annotations

import re

from ai.chains.base import Chain, ChainState, ChainStep
from ai.chatbot.base import ChatbotClient
from ai.prompts import default_registry
from ai.search.base import Retriever

INTENTS = ("returns", "shipping", "warranty", "support_hours", "payments", "out_of_scope")
HANDOFF_MESSAGE = "I can only help with Sauce Demo Store orders and policies. Let me connect you with a human agent."


class IntentStep(ChainStep):
    """Routes the question to one intent label using the ``intent_classifier`` prompt.

    Output normalisation is part of the step's contract: models add punctuation or
    capitals, so the step maps the raw reply onto the closed label set. Anything
    unrecognised becomes ``out_of_scope``, the safe default.
    """

    name = "intent"

    def __init__(self, chatbot: ChatbotClient) -> None:
        """Create the IntentStep; arguments are described in the class docstring."""
        self.chatbot = chatbot
        self.prompt = default_registry().get("intent_classifier")

    @staticmethod
    def normalise(raw: str) -> str:
        """Map a free-form model reply onto one of :data:`INTENTS`."""
        cleaned = re.sub(r"[^a-z_ ]", "", raw.lower()).strip().replace(" ", "_")
        for label in INTENTS:
            if cleaned == label or cleaned.startswith(label):
                return label
        for label in INTENTS:
            if label in cleaned:
                return label
        return "out_of_scope"

    def run(self, state: ChainState) -> str:
        """Classify ``state.question`` and store the label in ``state.intent``."""
        raw = self.chatbot.run_prompt(self.prompt, question=state.question).text
        state.intent = self.normalise(raw)
        return state.intent


class HandoffStep(ChainStep):
    """Short-circuits off-topic requests to a human, without spending more LLM calls."""

    name = "handoff"

    def run(self, state: ChainState) -> str | None:
        """Halt the chain with a hand-off message when the intent is out of scope."""
        if state.intent == "out_of_scope":
            state.answer = HANDOFF_MESSAGE
            state.halted = True
            return HANDOFF_MESSAGE
        return None


class RewriteStep(ChainStep):
    """Condenses a chatty question into a keyword query with the ``query_rewriter`` prompt."""

    name = "rewrite"

    def __init__(self, chatbot: ChatbotClient) -> None:
        """Create the RewriteStep; arguments are described in the class docstring."""
        self.chatbot = chatbot
        self.prompt = default_registry().get("query_rewriter")

    def run(self, state: ChainState) -> str:
        """Store the rewritten query in ``state.query``, falling back to the question if it's empty."""
        rewritten = self.chatbot.run_prompt(self.prompt, question=state.question).text.strip().strip('"')
        state.query = rewritten or state.question
        return state.query


class RetrieveStep(ChainStep):
    """Searches the knowledge base with the rewritten query.

    Args:
        retriever: Any :class:`~ai.search.base.Retriever`.
        k: Passages to keep.
    """

    name = "retrieve"

    def __init__(self, retriever: Retriever, k: int = 3) -> None:
        """Create the RetrieveStep; arguments are described in the class docstring."""
        self.retriever = retriever
        self.k = k

    def run(self, state: ChainState) -> list[str]:
        """Fill ``state.documents`` and ``state.document_ids``."""
        results = self.retriever.search(state.query or state.question, k=self.k)
        state.documents = [r.document.text for r in results]
        state.document_ids = [r.document.id for r in results]
        return state.document_ids


class AnswerStep(ChainStep):
    """Generates the final grounded answer from the retrieved passages."""

    name = "answer"

    def __init__(self, chatbot: ChatbotClient) -> None:
        """Create the AnswerStep; arguments are described in the class docstring."""
        self.chatbot = chatbot

    def run(self, state: ChainState) -> str:
        """Answer the *original* question (not the rewrite) from ``state.documents``."""
        state.answer = self.chatbot.ask(state.question, state.documents).text
        return state.answer


def build_support_chain(chatbot: ChatbotClient, retriever: Retriever, k: int = 3) -> Chain:
    """Assemble the production support chain from its steps."""
    return Chain(
        [
            IntentStep(chatbot),
            HandoffStep(),
            RewriteStep(chatbot),
            RetrieveStep(retriever, k=k),
            AnswerStep(chatbot),
        ]
    )
