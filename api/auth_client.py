from playwright.sync_api import APIResponse

from api.base_client import BaseClient


class AuthClient(BaseClient):
    def create_token_response(self, username: str, password: str) -> APIResponse:
        return self.post("/auth", data={"username": username, "password": password})

    def create_token(self, username: str, password: str) -> str:
        response = self.create_token_response(username, password)
        body = response.json()
        if "token" not in body:
            raise RuntimeError(f"Auth failed: {body}")
        return body["token"]
