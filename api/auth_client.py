"""Service object for Restful Booker's ``/auth`` endpoint."""
from playwright.sync_api import APIResponse

from api.base_client import BaseClient


class AuthClient(BaseClient):
    """Creates API tokens."""

    def create_token_response(self, username: str, password: str) -> APIResponse:
        """POST credentials and return the raw response (for negative tests)."""
        return self.post("/auth", data={"username": username, "password": password})

    def create_token(self, username: str, password: str) -> str:
        """Return a token for valid credentials.

        Raises:
            RuntimeError: If the API rejects the credentials. Restful Booker signals
                this in the body with HTTP 200, so the status alone isn't enough.
        """
        response = self.create_token_response(username, password)
        body = response.json()
        if "token" not in body:
            raise RuntimeError(f"Auth failed: {body}")
        return body["token"]
