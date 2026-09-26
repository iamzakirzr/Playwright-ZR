"""Fixtures for the AI agent suite: a live shop-assistant server and its HTTP client.

The FastAPI app runs in-process on a background thread (uvicorn), so tests
talk to it over real HTTP exactly like a front end would. No Docker needed.
"""

from __future__ import annotations

import socket
import threading
import time
import uuid

import pytest
import uvicorn

from api import ShopAssistantClient


def _free_port() -> int:
    """Ask the OS for an unused TCP port."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def assistant_url(require_ollama_model, settings) -> str:
    """Start the shop assistant on a free port for the whole session; yield its base URL."""
    require_ollama_model(settings.chatbot_model)
    port = _free_port()
    server = uvicorn.Server(uvicorn.Config("apps.shop_assistant.main:app", host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.time() + 60
    while not server.started:
        if time.time() > deadline:
            raise RuntimeError("shop assistant did not start within 60s")
        time.sleep(0.1)
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=10)


@pytest.fixture(scope="session")
def assistant(playwright, assistant_url) -> ShopAssistantClient:
    """Service object for the running assistant (Playwright HTTP client, generous timeout for CPU LLMs)."""
    ctx = playwright.request.new_context(base_url=assistant_url, timeout=300_000)
    yield ShopAssistantClient(ctx)
    ctx.dispose()


@pytest.fixture
def session_id(assistant) -> str:
    """A fresh conversation per test, reset afterwards so tests never share cart state."""
    sid = f"t-{uuid.uuid4().hex[:10]}"
    yield sid
    assistant.reset(sid)
