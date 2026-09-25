"""Chatbot abstraction.

Tests depend on this protocol, not on a vendor. Swap in an OpenAI-compatible,
HF Inference, or browser-driven (UI POM) adapter without touching tests.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class ChatResponse:
    text: str
    model: str
    latency_ms: float
    raw: dict = field(default_factory=dict, repr=False)


class ChatbotClient(Protocol):
    def ask(self, question: str, context: list[str] | None = None) -> ChatResponse: ...

    def is_available(self) -> bool: ...
