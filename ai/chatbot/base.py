"""Chatbot abstraction layer.

Design
------
``ChatbotClient`` is an abstract base class using the **Template Method**
pattern: the public :meth:`ChatbotClient.ask` builds a grounded prompt, times
the call and delegates the transport to the abstract :meth:`complete`.
Concrete adapters (Ollama over HTTP, a browser-driven chat widget, a scripted
fake for unit tests, a guard-rail decorator) only implement ``complete`` and
``is_available``. Tests depend on this interface, never on a vendor.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from ai.prompts import PromptTemplate, default_registry


@dataclass(frozen=True)
class ChatResponse:
    """One model reply plus the telemetry needed for non-functional checks.

    Attributes:
        text: The assistant message, stripped of surrounding whitespace.
        model: Model identifier reported by the backend.
        latency_ms: Wall-clock time of the call in milliseconds.
        prompt_tokens: Tokens consumed by the prompt (0 if the backend doesn't report it).
        completion_tokens: Tokens generated in the reply (0 if unknown).
        raw: Backend-specific payload, kept for debugging.
    """

    text: str
    model: str
    latency_ms: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    raw: dict = field(default_factory=dict, repr=False)


class ChatbotClient(ABC):
    """Abstract chatbot. Subclasses implement the transport; this class owns prompting.

    Args:
        grounded_prompt: Template used by :meth:`ask` when context is supplied.
        open_prompt: Template used by :meth:`ask` when no context is supplied.
        canary: Secret token planted in the system prompt. It must never appear in
            output; red-team tests use it to detect system-prompt leakage.
    """

    def __init__(
        self,
        grounded_prompt: PromptTemplate | None = None,
        open_prompt: PromptTemplate | None = None,
        canary: str = "",
    ) -> None:
        """Create the ChatbotClient; arguments are described in the class docstring."""
        registry = default_registry()
        self.grounded_prompt = grounded_prompt or registry.get("grounded_qa")
        self.open_prompt = open_prompt or registry.get("open_qa")
        self.canary = canary

    # ------------------------------------------------------------------ #
    # Abstract transport
    # ------------------------------------------------------------------ #
    @abstractmethod
    def complete(self, system: str, user: str, *, json_mode: bool = False) -> ChatResponse:
        """Send one system + user message pair and return the reply.

        Args:
            system: System prompt (instructions, context, rules).
            user: The end-user message.
            json_mode: Ask the backend to constrain output to valid JSON when supported.
        """

    @abstractmethod
    def is_available(self) -> bool:
        """Return True when the backend and model are reachable, so tests can skip cleanly."""

    # ------------------------------------------------------------------ #
    # Template method
    # ------------------------------------------------------------------ #
    def ask(self, question: str, context: list[str] | None = None) -> ChatResponse:
        """Answer ``question``; when ``context`` is given, answer only from it (RAG style).

        Args:
            question: The user's question.
            context: Retrieved passages the answer must be grounded in.

        Returns:
            The model's :class:`ChatResponse`.
        """
        if context:
            prompt = self.grounded_prompt.render(
                context="\n".join(f"- {c}" for c in context),
                canary=self.canary,
                question=question,
            )
        else:
            prompt = self.open_prompt.render(canary=self.canary, question=question)
        return self.complete(prompt.system, prompt.user)

    def run_prompt(self, template: PromptTemplate, *, json_mode: bool = False, **variables) -> ChatResponse:
        """Render any registered prompt template and send it.

        Args:
            template: The prompt to render.
            json_mode: Constrain the output to JSON when the backend supports it.
            **variables: Values for the template placeholders.
        """
        prompt = template.render(**variables)
        return self.complete(prompt.system, prompt.user, json_mode=json_mode)
