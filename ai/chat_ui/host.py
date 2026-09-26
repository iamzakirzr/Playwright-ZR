"""Serve the chat widget inside Playwright, with no web server.

``ChatHost`` uses Playwright network interception (``page.route``) to:

* serve ``index.html`` at a fake origin (``http://chatbot.local``), and
* answer the widget's ``/api/chat`` calls in one of two **modes**:
  - ``proxy``: forward to the real Ollama server (live end-to-end tests);
  - ``stub``: return a canned reply or HTTP error (fast, deterministic UI tests).

Every request the page makes is recorded, so tests can assert on the API
contract between front end and back end.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from playwright.sync_api import Page, Request, Route

CHAT_ORIGIN = "http://chatbot.local"
INDEX_HTML = Path(__file__).with_name("index.html")


class ChatHost:
    """Installs routes that serve the widget and its backend on one page.

    Args:
        page: The Playwright page to install routes on.
        ollama_host: Real Ollama base URL, used in ``proxy`` mode.
    """

    def __init__(self, page: Page, ollama_host: str) -> None:
        """Create the ChatHost; arguments are described in the class docstring."""
        self.page = page
        self.ollama_host = ollama_host.rstrip("/")
        self.requests: list[dict] = []
        self._backend: Callable[[Route, Request], None] = self._proxy
        self._held: list[Route] = []

    # -- installation -------------------------------------------------------
    def install(self) -> ChatHost:
        """Register the HTML and API routes; call before navigating."""
        self.page.route(f"{CHAT_ORIGIN}/", self._serve_html)
        self.page.route(f"{CHAT_ORIGIN}/api/chat", self._handle_api)
        return self

    def _serve_html(self, route: Route, request: Request) -> None:
        """Fulfil the page request with the local widget HTML."""
        route.fulfill(status=200, content_type="text/html", body=INDEX_HTML.read_text())

    def _handle_api(self, route: Route, request: Request) -> None:
        """Record the request body, then delegate to the active backend mode."""
        self.requests.append(json.loads(request.post_data or "{}"))
        self._backend(route, request)

    # -- backend modes ------------------------------------------------------
    #: Browser-only headers stripped before forwarding. Ollama answers 403 to any
    #: request whose Origin isn't on its allow-list, and a real reverse proxy
    #: would drop these too.
    BROWSER_ONLY_HEADERS = frozenset({"origin", "referer", "sec-fetch-site", "sec-fetch-mode", "sec-fetch-dest"})

    @classmethod
    def forward_headers(cls, headers: dict[str, str]) -> dict[str, str]:
        """The subset of browser request headers that is safe to forward to the model server."""
        return {k: v for k, v in headers.items() if k.lower() not in cls.BROWSER_ONLY_HEADERS}

    def _proxy(self, route: Route, request: Request) -> None:
        """Forward to the real Ollama ``/api/chat`` (minus browser-only headers) and relay the response."""
        headers = self.forward_headers(request.headers)
        response = route.fetch(url=f"{self.ollama_host}/api/chat", headers=headers, timeout=180_000)
        route.fulfill(response=response)

    def use_proxy(self) -> ChatHost:
        """Switch to live mode: requests reach the real model."""
        self._backend = self._proxy
        return self

    def use_stub(self, reply: str = "stub reply", status: int = 200) -> ChatHost:
        """Switch to stub mode: every request gets ``reply`` (or an error when ``status`` >= 400)."""

        def stub(route: Route, request: Request) -> None:
            """Fulfil with a canned Ollama-shaped payload."""
            if status >= 400:
                route.fulfill(status=status, body="backend error")
            else:
                route.fulfill(status=200, content_type="application/json", body=json.dumps({"message": {"content": reply}}))

        self._backend = stub
        return self

    def use_hold(self) -> ChatHost:
        """Switch to hold mode: requests hang until :meth:`release` (for loading-state tests)."""
        self._backend = lambda route, request: self._held.append(route)
        return self

    def release(self, reply: str = "released reply") -> None:
        """Answer every held request with ``reply``."""
        while self._held:
            self._held.pop(0).fulfill(
                status=200, content_type="application/json", body=json.dumps({"message": {"content": reply}})
            )

    @property
    def last_request(self) -> dict:
        """The most recent ``/api/chat`` request body sent by the page."""
        return self.requests[-1]
