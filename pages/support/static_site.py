"""Serve a local folder, plus fake API endpoints, at a made-up origin with no web server.

``StaticSite`` is Playwright network interception (``context.route``) packaged for reuse:

* files under ``root`` are served at ``origin`` (``/`` maps to ``index.html``);
* API endpoints are Python callables registered per method and path;
* every request is recorded, so tests can assert on what the page sent.

Routes are installed on the **browser context**, not the page, so pop-ups and new tabs
opened by the site are served too. Because the origin is a real-looking ``https://`` URL (a
secure context, which geolocation and downloads require), cookies and ``localStorage`` behave
as on a deployed site; with ``file://`` they don't.

Example::

    site = StaticSite(context, Path("apps/playground/site"))
    site.json("GET", "/api/products", [{"name": "Backpack", "price": 29.99}])
    site.install()
    page.goto(site.url("/products.html"))
"""

from __future__ import annotations

import json
import mimetypes
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import BrowserContext, Request, Route


@dataclass(frozen=True)
class RecordedRequest:
    """One request the page made to the site.

    Attributes:
        method: HTTP method.
        path: URL path, without query string.
        query: Parsed query string (each key maps to a list of values).
        body: Parsed JSON body, raw text, or None.
        headers: All request headers, lower-case names, including ``cookie``.
    """

    method: str
    path: str
    query: dict[str, list[str]]
    body: Any
    headers: dict[str, str] = field(default_factory=dict)

    def cookie(self, name: str) -> str | None:
        """Value of cookie ``name`` sent with the request, or None."""
        for pair in self.headers.get("cookie", "").split(";"):
            key, _, value = pair.strip().partition("=")
            if key == name:
                return value
        return None


@dataclass
class ApiResponse:
    """What an API handler returns.

    Attributes:
        body: ``dict``/``list`` (sent as JSON), ``str`` or ``bytes``.
        status: HTTP status code.
        headers: Extra response headers (e.g. ``Set-Cookie``).
        content_type: Defaults to JSON for dict/list, text otherwise.
    """

    body: Any = None
    status: int = 200
    headers: dict[str, str] = field(default_factory=dict)
    content_type: str | None = None


Handler = Callable[[RecordedRequest], ApiResponse]


class StaticSite:
    """A folder of HTML plus fake endpoints, served inside Playwright.

    Args:
        context: Browser context to install routes on.
        root: Folder with the site's files.
        origin: Fake origin the site appears at.
    """

    def __init__(self, context: BrowserContext, root: Path, origin: str = "https://playground.local") -> None:
        """Store configuration; nothing is routed until :meth:`install`."""
        self.context = context
        self.root = Path(root)
        self.origin = origin.rstrip("/")
        self.requests: list[RecordedRequest] = []
        self._api: dict[tuple[str, str], Handler] = {}

    # -- configuration -------------------------------------------------------
    def api(self, method: str, path: str, handler: Handler) -> StaticSite:
        """Register ``handler`` for ``method path``; returns self so calls can chain."""
        self._api[(method.upper(), path)] = handler
        return self

    def json(self, method: str, path: str, data: Any, status: int = 200) -> StaticSite:
        """Shortcut: always answer ``method path`` with ``data`` as JSON."""
        return self.api(method, path, lambda _request: ApiResponse(data, status))

    def install(self) -> StaticSite:
        """Start serving; call before the first navigation."""
        self.context.route(f"{self.origin}/**", self._handle)
        return self

    def url(self, path: str = "/") -> str:
        """Absolute URL of ``path`` on this site."""
        return f"{self.origin}{path}"

    def requests_to(self, path: str) -> list[RecordedRequest]:
        """Recorded requests whose path is exactly ``path``."""
        return [r for r in self.requests if r.path == path]

    # -- serving -----------------------------------------------------------------
    def _handle(self, route: Route, request: Request) -> None:
        """Record the request, then answer from an API handler, a file, or with 404."""
        parts = urlsplit(request.url)
        recorded = RecordedRequest(request.method, parts.path, parse_qs(parts.query), self._body(request), self._headers(request))
        self.requests.append(recorded)

        handler = self._api.get((request.method, parts.path))
        if handler is not None:
            self._fulfil(route, handler(recorded))
            return
        file = self.root / (parts.path.lstrip("/") or "index.html")
        if file.is_file() and self.root.resolve() in file.resolve().parents:
            content_type = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
            route.fulfill(status=200, content_type=content_type, body=file.read_bytes())
        else:
            route.fulfill(status=404, content_type="text/plain", body=f"Not found: {parts.path}")

    def _headers(self, request: Request) -> dict[str, str]:
        """Request headers plus a ``cookie`` header rebuilt from the context's cookie jar.

        ``request.headers`` omits cookies, and ``request.all_headers()`` hangs inside a route
        handler (it waits for network data that only arrives after the route is released).
        """
        headers = dict(request.headers)
        cookies = self.context.cookies(request.url)
        if cookies:
            headers["cookie"] = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
        return headers

    @staticmethod
    def _body(request: Request) -> Any:
        """The request body as JSON when possible, else text, else None."""
        data = request.post_data
        if not data:
            return None
        try:
            return json.loads(data)
        except ValueError:
            return data

    @staticmethod
    def _fulfil(route: Route, response: ApiResponse) -> None:
        """Turn an :class:`ApiResponse` into a fulfilled route."""
        body = response.body
        content_type = response.content_type
        if isinstance(body, (dict, list)):
            body, content_type = json.dumps(body), content_type or "application/json"
        route.fulfill(
            status=response.status,
            headers=response.headers,
            content_type=content_type or "text/plain",
            body=body if body is not None else "",
        )
