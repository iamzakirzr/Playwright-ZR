"""Screen objects: the mobile equivalent of page objects.

The same rules as ``pages/base_page.py`` apply: screens hold locators and
actions, tests hold assertions. A locator is a ``(strategy, value)`` tuple,
so one screen class can target mobile web (CSS) or a native app
(accessibility id, resource id) without changing its methods.

Appium / Selenium are imported lazily so suites that omit the ``mobile`` extra
can still import this module during collection without ``ModuleNotFoundError``.
"""

from __future__ import annotations

from typing import Any

from reporting import step

Locator = tuple[str, str]

# AppiumBy string values — keep import-time free of the Appium package.
_CSS_SELECTOR = "css selector"
_ACCESSIBILITY_ID = "accessibility id"


def css(selector: str) -> Locator:
    """Locator for mobile web (Chrome on the device)."""
    return (_CSS_SELECTOR, selector)


def accessibility_id(value: str) -> Locator:
    """Locator for native apps: content-desc on Android, accessibilityIdentifier on iOS."""
    return (_ACCESSIBILITY_ID, value)


def _selenium_wait_tools() -> tuple[Any, Any]:
    """Import Selenium wait helpers only when a screen method runs."""
    try:
        from selenium.webdriver.support import expected_conditions as ec
        from selenium.webdriver.support.ui import WebDriverWait
    except ImportError as exc:  # pragma: no cover - mobile extra absent
        raise ImportError("selenium is not installed. Install the mobile extra: pip install -e '.[mobile]'") from exc
    return ec, WebDriverWait


class BaseScreen:
    """Waits and actions shared by every screen.

    Args:
        driver: An Appium session from :class:`~mobile.driver_factory.AppiumDriverFactory`.
        timeout: Seconds to wait for elements.
    """

    def __init__(self, driver, timeout: float = 20) -> None:
        """Keep the driver and a reusable explicit wait."""
        _, web_driver_wait = _selenium_wait_tools()
        self.driver = driver
        self.wait = web_driver_wait(driver, timeout)

    def find(self, locator: Locator):
        """Wait until the element is visible and return it."""
        ec, _ = _selenium_wait_tools()
        return self.wait.until(ec.visibility_of_element_located(locator))

    def find_all(self, locator: Locator) -> list:
        """All currently matching elements (no wait)."""
        return self.driver.find_elements(*locator)

    def tap(self, locator: Locator) -> None:
        """Wait until clickable, then tap."""
        ec, _ = _selenium_wait_tools()
        self.wait.until(ec.element_to_be_clickable(locator)).click()

    def type(self, locator: Locator, text: str) -> None:
        """Clear the field and type ``text``."""
        element = self.find(locator)
        element.clear()
        element.send_keys(text)

    def is_visible(self, locator: Locator) -> bool:
        """True if at least one matching element is displayed."""
        return any(e.is_displayed() for e in self.find_all(locator))

    @step("Rotate device to {orientation}")
    def rotate(self, orientation: str) -> None:
        """Rotate the device: ``"LANDSCAPE"`` or ``"PORTRAIT"``."""
        self.driver.orientation = orientation
