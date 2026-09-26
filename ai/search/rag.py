"""Retrieval-Augmented Generation: search, then answer from what was found."""

from __future__ import annotations

from dataclasses import dataclass

from ai.chatbot.base import ChatbotClient, ChatResponse
from ai.search.base import Retriever, SearchResult

NO_ANSWER = "I don't know based on the provided information."


@dataclass(frozen=True)
class RagAnswer:
    """The generated answer plus the evidence it was generated from."""

    question: str
    response: ChatResponse | None
    results: list[SearchResult]

    @property
    def text(self) -> str:
        """The answer text, or the standard abstention when nothing was retrieved."""
        return self.response.text if self.response else NO_ANSWER

    @property
    def contexts(self) -> list[str]:
        """Retrieved passage texts, in rank order (DeepEval's ``retrieval_context``)."""
        return [r.document.text for r in self.results]

    @property
    def document_ids(self) -> list[str]:
        """Retrieved document ids, in rank order."""
        return [r.document.id for r in self.results]


class RagPipeline:
    """Composes a :class:`Retriever` with a :class:`ChatbotClient` (dependency injection).

    Args:
        retriever: Any retrieval strategy.
        chatbot: Any chatbot.
        k: Passages to retrieve per question.
        min_score: Retrieval floor. Below it, the pipeline abstains without calling the LLM,
            which saves cost and removes one hallucination path.
    """

    def __init__(self, retriever: Retriever, chatbot: ChatbotClient, k: int = 3, min_score: float | None = None) -> None:
        """Create the RagPipeline; arguments are described in the class docstring."""
        self.retriever = retriever
        self.chatbot = chatbot
        self.k = k
        self.min_score = min_score

    def answer(self, question: str) -> RagAnswer:
        """Retrieve passages for ``question`` and generate a grounded answer."""
        results = self.retriever.search(question, k=self.k, min_score=self.min_score)
        if not results:
            return RagAnswer(question, None, [])
        response = self.chatbot.ask(question, [r.document.text for r in results])
        return RagAnswer(question, response, results)
