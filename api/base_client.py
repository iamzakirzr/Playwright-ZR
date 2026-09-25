"""Service-object base: the API-layer equivalent of a page object.

Wraps Playwright's ``APIRequestContext`` so API tests share tracing, base URL
and auth handling with the UI tests, and expose intent-level methods
(``create_booking``) instead of raw HTTP calls.
"""
from __future__ import annotations

from typing import Any

from playwright.sync_api import APIRequestContext, APIResponse


class BaseClient:
    """Thin HTTP wrapper with default JSON headers; subclasses add one method per endpoint.

    Args:
        request: A Playwright request context created with a ``base_url``.
    """

    def __init__(self, request: APIRequestContext) -> None:
        """Store the request context and default JSON headers."""
        self.request = request
        self._headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def set_header(self, key: str, value: str) -> None:
        """Add or replace a header sent on every later request (for example an auth cookie)."""
        self._headers[key] = value

    def _merge(self, headers: dict[str, str] | None) -> dict[str, str]:
        """Default headers overlaid with per-call ``headers``."""
        return {**self._headers, **(headers or {})}

    def get(self, path: str, *, params: dict[str, Any] | None = None, headers=None) -> APIResponse:
        """HTTP GET ``path`` with optional query ``params``."""
        return self.request.get(path, params=params, headers=self._merge(headers))

    def post(self, path: str, *, data: Any = None, headers=None) -> APIResponse:
        """HTTP POST ``data`` (serialised as JSON) to ``path``."""
        return self.request.post(path, data=data, headers=self._merge(headers))

    def put(self, path: str, *, data: Any = None, headers=None) -> APIResponse:
        """HTTP PUT (full replacement) of ``path``."""
        return self.request.put(path, data=data, headers=self._merge(headers))

    def patch(self, path: str, *, data: Any = None, headers=None) -> APIResponse:
        """HTTP PATCH (partial update) of ``path``."""
        return self.request.patch(path, data=data, headers=self._merge(headers))

    def delete(self, path: str, *, headers=None) -> APIResponse:
        """HTTP DELETE ``path``."""
        return self.request.delete(path, headers=self._merge(headers))
