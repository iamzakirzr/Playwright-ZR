"""Chatbot adapter that talks to the model *through the browser UI*.

Because ``UiChatbot`` is a :class:`ChatbotClient`, every metric, dataset and
red-team attack written for the API adapter runs unchanged through the real
chat widget. That catches bugs that only exist in the UI layer: truncation,
escaping, lost messages.
"""

from __future__ import annotations

import time

from ai.chatbot.base import ChatbotClient, ChatResponse
from pages.chat_page import ChatPage


class UiChatbot(ChatbotClient):
    """Drives :class:`~pages.chat_page.ChatPage` to get answers.

    Args:
        chat_page: A loaded chat page whose backend is live (``ChatHost.use_proxy``).
        model: Model name the widget should request.
        **kwargs: Forwarded to :class:`ChatbotClient` (prompts, canary).
    """

    def __init__(self, chat_page: ChatPage, model: str, **kwargs) -> None:
        """Create the UiChatbot; arguments are described in the class docstring."""
        super().__init__(**kwargs)
        self.chat_page = chat_page
        self.model = model

    def is_available(self) -> bool:
        """Available when the chat input is on screen and enabled."""
        return self.chat_page.input.is_enabled()

    def complete(self, system: str, user: str, *, json_mode: bool = False) -> ChatResponse:
        """Configure the widget's system prompt, send ``user`` through the UI, and read the reply bubble.

        ``json_mode`` is ignored: the widget has no JSON mode, so UI tests stay on plain answers.
        """
        self.chat_page.configure(system=system, model=self.model)
        started = time.perf_counter()
        text = self.chat_page.send_and_wait(user)
        return ChatResponse(text=text, model=self.model, latency_ms=(time.perf_counter() - started) * 1000)
