"""Deterministic fake chatbot for unit-testing prompt and chain logic without a model.

This is a **test double** (stub + spy): it returns canned replies and records
every call, so chain-routing and prompt-rendering tests run in milliseconds
and never flake. Because it is a real ``ChatbotClient`` subclass, any code
that works with the live bot works with this one (Liskov substitution).
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from ai.chatbot.base import ChatbotClient, ChatResponse


@dataclass(frozen=True)
class RecordedCall:
    """One call captured by :class:`ScriptedChatbot`."""

    system: str
    user: str
    json_mode: bool


class ScriptedChatbot(ChatbotClient):
    """Chatbot whose replies come from a function or a fixed list.

    Args:
        responder: Either a callable ``(system, user) -> str`` or a list of replies
            returned in order.
        **kwargs: Forwarded to :class:`ChatbotClient`.
    """

    def __init__(self, responder: Callable[[str, str], str] | list[str], **kwargs) -> None:
        """Create the ScriptedChatbot; arguments are described in the class docstring."""
        super().__init__(**kwargs)
        self._responder = responder
        self._queue = list(responder) if isinstance(responder, list) else None
        self.calls: list[RecordedCall] = []

    def is_available(self) -> bool:
        """A scripted bot is always available."""
        return True

    def complete(self, system: str, user: str, *, json_mode: bool = False) -> ChatResponse:
        """Record the call and return the next scripted reply.

        Raises:
            AssertionError: If a list-based script runs out of replies (the chain
                made more model calls than the test expected).
        """
        self.calls.append(RecordedCall(system, user, json_mode))
        if self._queue is not None:
            assert self._queue, f"ScriptedChatbot ran out of replies at call #{len(self.calls)}"
            text = self._queue.pop(0)
        else:
            text = self._responder(system, user)
        return ChatResponse(text=text, model="scripted", latency_ms=0.0)
