"""Base class for all page objects.

Page Object Model rules used in this framework
----------------------------------------------
* A page object encapsulates *how* to interact with a page: locators, waits, navigation.
* Tests own *what* is asserted. The only assertion allowed inside a page object
  is :meth:`BasePage.expect_loaded`, which guards the page's identity.
* Methods speak the user's language (``login_as``, ``add_to_cart``), not the DOM's.
* Locators are created once in ``__init__``. Playwright locators are lazy, so
  this costs nothing and keeps selectors in one place.
"""
from __future__ import annotations

from playwright.sync_api import Locator, Page


class BasePage:
    """Shared plumbing for every page object (inheritance root).

    Args:
        page: The Playwright page (browser tab) to drive.
        base_url: Scheme and host of the application, e.g. ``https://www.saucedemo.com``.
    """

    #: Path relative to ``base_url``. Subclasses override.
    path: str = "/"

    def __init__(self, page: Page, base_url: str) -> None:
        """Store the page and normalise the base URL (no trailing slash)."""
        self.page = page
        self.base_url = base_url.rstrip("/")

    # -- navigation ---------------------------------------------------------
    def open(self):
        """Navigate to ``base_url + path`` and return ``self`` for chaining (``page.open().login_as(...)``)."""
        self.page.goto(f"{self.base_url}{self.path}")
        return self

    @property
    def url(self) -> str:
        """The browser's current URL."""
        return self.page.url

    # -- helpers ------------------------------------------------------------
    def by_test_id(self, test_id: str) -> Locator:
        """Locate by Sauce Demo's ``data-test`` attribute (not Playwright's default ``data-testid``)."""
        return self.page.locator(f"[data-test='{test_id}']")

    def expect_loaded(self):
        """Assert this is the right page. Subclasses override with an identity check; returns ``self``."""
        return self
