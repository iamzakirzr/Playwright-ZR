"""Fixtures for the Playwright essentials suite (the playground app lives in ``apps/playground``)."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from apps.playground import PRODUCTS, serve_playground
from pages.support import StaticSite


@pytest.fixture
def site(context) -> StaticSite:
    """Playground on the test's default browser context (pytest-playwright's ``context`` fixture)."""
    return serve_playground(context)


@pytest.fixture
def base_url_playground(site) -> str:
    """Origin to pass to the playground page objects."""
    return site.origin


@pytest.fixture
def real_products_api():
    """A real HTTP server on localhost returning the product list; yields its URL.

    Used where a test needs genuine network traffic (``route.fetch``) rather than a mock.
    """

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802 - name required by BaseHTTPRequestHandler
            body = json.dumps(PRODUCTS).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            """Keep test output quiet."""

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}/api/products"
    server.shutdown()
