"""Base class for all page objects.

Page objects encapsulate *how* to interact with a page (locators, waits,
navigation). Tests own *what* is asserted. The only assertion allowed in a
page object is `expect_loaded()`, which guards the page's identity.
"""
from __future__ import annotations

from playwright.sync_api import Locator, Page, expect


class BasePage:
    #: Path relative to the base URL. Subclasses override.
    path: str = "/"

    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url.rstrip("/")

    # -- navigation ---------------------------------------------------------
    def open(self):
        self.page.goto(f"{self.base_url}{self.path}")
        return self

    @property
    def url(self) -> str:
        return self.page.url

    # -- helpers ------------------------------------------------------------
    def by_test_id(self, test_id: str) -> Locator:
        """Sauce Demo uses `data-test`, not the Playwright default `data-testid`."""
        return self.page.locator(f"[data-test='{test_id}']")

    def expect_loaded(self):
        """Override in subclasses with a page-identity check."""
        return self
