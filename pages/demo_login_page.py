"""Page object for the local demo login page used to teach self-healing locators.

It is written against v1 of ``tests/ai/healing/html/login_v1.html``. Every element
is declared with :meth:`BasePage.healable`, so it keeps working when v2 renames them.
"""
from __future__ import annotations

from pathlib import Path

from pages.base_page import BasePage

HTML_DIR = Path(__file__).resolve().parents[1] / "tests" / "ai" / "healing" / "html"


class DemoLoginPage(BasePage):
    """Login form whose elements heal themselves.

    Args:
        page: Playwright page.
        healer: Selector healer (an LLM healer, or a fake in unit tests).
        cache: Healing cache.
    """

    def __init__(self, page, healer, cache):
        """Declare healable elements with their v1 selectors."""
        super().__init__(page, "file://", healer=healer, cache=cache)
        self.username = self.healable("username", "[data-test='username']", "the Username text input")
        self.password = self.healable("password", "[data-test='password']", "the Password input")
        self.login_button = self.healable("login_button", "[data-test='login-button']", "the Login submit button")

    def load(self, version: str) -> "DemoLoginPage":
        """Open ``login_<version>.html`` from disk."""
        self.page.goto((HTML_DIR / f"login_{version}.html").as_uri())
        return self

    def login_as(self, username: str, password: str) -> None:
        """Fill and submit the form (each element resolves, healing if needed)."""
        self.username.resolve().fill(username)
        self.password.resolve().fill(password)
        self.login_button.resolve().click()

    def result_text(self) -> str:
        """The welcome message (plain text match, independent of attribute renames)."""
        return self.page.get_by_text("Welcome,").inner_text()
