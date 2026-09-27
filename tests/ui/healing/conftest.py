"""Fixtures for self-healing locator tests.

Offline tests use a fake healer. The live end-to-end test needs the same Ollama
``chatbot`` fixture the AI suites use; it is defined here so healing can live under
``tests/ui/`` without depending on ``tests/ai/conftest.py``.
"""

from __future__ import annotations

import pytest

from ai.chatbot import OllamaChatbot
from pages.healing import HealingCache


@pytest.fixture
def healing_cache(tmp_path) -> HealingCache:
    """A fresh healing cache file per test."""
    return HealingCache(tmp_path / "healed_locators.json")


@pytest.fixture(scope="session")
def chatbot(ollama_request, require_ollama_model, settings) -> OllamaChatbot:
    """Local Ollama chatbot for the live healing path (skips when unavailable)."""
    require_ollama_model(settings.chatbot_model)
    return OllamaChatbot(
        ollama_request,
        model=settings.chatbot_model,
        temperature=settings.chatbot_temperature,
        seed=settings.chatbot_seed,
        timeout_s=settings.chatbot_timeout_s,
        canary=settings.canary_token,
    )
