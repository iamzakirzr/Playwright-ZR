"""Service-object base: the API-layer equivalent of a page object.

Wraps Playwright's APIRequestContext so API tests share tracing, base URL and
auth handling with UI tests, and exposes intent-level methods to tests.
"""
from __future__ import annotations

from typing import Any

from playwright.sync_api import APIRequestContext, APIResponse


class BaseClient:
    def __init__(self, request: APIRequestContext) -> None:
        self.request = request
        self._headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def set_header(self, key: str, value: str) -> None:
        self._headers[key] = value

    def _merge(self, headers: dict[str, str] | None) -> dict[str, str]:
        return {**self._headers, **(headers or {})}

    def get(self, path: str, *, params: dict[str, Any] | None = None, headers=None) -> APIResponse:
        return self.request.get(path, params=params, headers=self._merge(headers))

    def post(self, path: str, *, data: Any = None, headers=None) -> APIResponse:
        return self.request.post(path, data=data, headers=self._merge(headers))

    def put(self, path: str, *, data: Any = None, headers=None) -> APIResponse:
        return self.request.put(path, data=data, headers=self._merge(headers))

    def patch(self, path: str, *, data: Any = None, headers=None) -> APIResponse:
        return self.request.patch(path, data=data, headers=self._merge(headers))

    def delete(self, path: str, *, headers=None) -> APIResponse:
        return self.request.delete(path, headers=self._merge(headers))
