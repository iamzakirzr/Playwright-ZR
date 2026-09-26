"""Base class for all page objects.

Page Object Model rules used in this framework
----------------------------------------------
* A page object encapsulates *how* to interact with a page: locators, waits, navigation.
* Tests own *what* is asserted. The only assertion allowed inside a page object
  is :meth:`BasePage.expect_loaded`, which guards the page's identity.
* Methods speak the user's language (``login_as``, ``add_to_cart``), not the DOM's.
* Locators are created once in ``__init__``. Playwright locators are lazy, so
  this costs nothing and keeps selectors in one place.
* Optional **self-healing**: pass a ``healer`` and ``cache`` and declare elements
  with :meth:`BasePage.healable`. Without them the page behaves exactly as before.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from playwright.sync_api import Locator, Page

from reporting import step

if TYPE_CHECKING:
    from pages.healing import HealingCache, LocatorHealer, SelfHealingLocator


class BasePage:
    """Shared plumbing for every page object (inheritance root).

    Args:
        page: The Playwright page (browser tab) to drive.
        base_url: Scheme and host of the application, e.g. ``https://www.saucedemo.com``.
        healer: Optional selector healer (e.g. ``LlmLocatorHealer``) enabling :meth:`healable`.
        cache: Healing cache, required together with ``healer``.
    """

    #: Path relative to ``base_url``. Subclasses override.
    path: str = "/"

    def __init__(
        self, page: Page, base_url: str, healer: "LocatorHealer | None" = None, cache: "HealingCache | None" = None
    ) -> None:
        """Store the page, normalise the base URL (no trailing slash) and keep optional healing support."""
        self.page = page
        self.base_url = base_url.rstrip("/")
        self.healer = healer
        self.cache = cache

    # -- navigation ---------------------------------------------------------
    @step("Open page")
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

    def healable(self, name: str, selector: str, description: str) -> "SelfHealingLocator":
        """Declare an element that heals itself if ``selector`` breaks.

        Args:
            name: Element name; combined with the class name to form the cache key.
            selector: Current CSS selector.
            description: What the element is, in words the healer can match ("the Login button").

        Raises:
            ValueError: If the page was created without a healer and cache.
        """
        from pages.healing import SelfHealingLocator

        if self.healer is None or self.cache is None:
            raise ValueError(f"{type(self).__name__} needs healer= and cache= to use healable()")
        return SelfHealingLocator(self.page, f"{type(self).__name__}.{name}", selector, description, self.healer, self.cache)

    def expect_loaded(self):
        """Assert this is the right page. Subclasses override with an identity check; returns ``self``."""
        return self
