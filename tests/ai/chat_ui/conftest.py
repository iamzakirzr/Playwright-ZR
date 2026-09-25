"""Fixtures for browser-driven chat widget tests."""
import pytest

from ai.chat_ui import CHAT_ORIGIN, ChatHost
from pages import ChatPage


@pytest.fixture
def chat_host(page, settings) -> ChatHost:
    """Route-based host for the widget; tests pick stub, hold or proxy mode."""
    return ChatHost(page, settings.ollama_host).install()


@pytest.fixture
def chat_page(page, chat_host) -> ChatPage:
    """The chat widget, opened and ready."""
    return ChatPage(page, CHAT_ORIGIN).open().expect_loaded()
