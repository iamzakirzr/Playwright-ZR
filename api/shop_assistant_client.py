"""Service object for the AI shop assistant's HTTP API (``apps/shop_assistant``)."""

from __future__ import annotations

from playwright.sync_api import APIResponse

from api.base_client import BaseClient
from reporting import attach_json, step


class ShopAssistantClient(BaseClient):
    """Talks to the assistant the way a front end would: chat, read the cart, reset the session."""

    def chat_response(self, session_id: str, message: str) -> APIResponse:
        """Raw ``POST /chat`` (for status-code and validation tests)."""
        return self.post("/chat", data={"session_id": session_id, "message": message})

    @step("Chat [{session_id}]: {message}")
    def chat(self, session_id: str, message: str) -> dict:
        """Send a message and return the parsed reply.

        Raises:
            AssertionError: If the API does not answer 200, with the body in the message.
        """
        response = self.chat_response(session_id, message)
        assert response.ok, f"/chat returned {response.status}: {response.text()}"
        body = response.json()
        attach_json(f"chat: {message[:50]}", {"message": message, **body})
        return body

    def cart(self, session_id: str) -> dict:
        """The session's cart as ``{"items": [...], "total": float}``."""
        return self.get(f"/cart/{session_id}").json()

    def reset(self, session_id: str) -> int:
        """Forget the session; returns the HTTP status (204 expected)."""
        return self.delete(f"/session/{session_id}").status

    def quantity_of(self, session_id: str, product: str) -> int:
        """How many of ``product`` are in the session's cart (0 if none)."""
        return next((i["quantity"] for i in self.cart(session_id)["items"] if i["product"] == product), 0)
