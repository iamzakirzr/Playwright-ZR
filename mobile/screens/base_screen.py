"""Screen objects: the mobile equivalent of page objects.

The same rules as ``pages/base_page.py`` apply: screens hold locators and
actions, tests hold assertions. A locator is a ``(strategy, value)`` tuple,
so one screen class can target mobile web (CSS) or a native app
(accessibility id, resource id) without changing its methods.
"""

from __future__ import annotations

from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from reporting import step

Locator = tuple[str, str]


def css(selector: str) -> Locator:
    """Locator for mobile web (Chrome on the device)."""
    return (AppiumBy.CSS_SELECTOR, selector)


def accessibility_id(value: str) -> Locator:
    """Locator for native apps: content-desc on Android, accessibilityIdentifier on iOS."""
    return (AppiumBy.ACCESSIBILITY_ID, value)


class BaseScreen:
    """Waits and actions shared by every screen.

    Args:
        driver: An Appium session from :class:`~mobile.driver_factory.AppiumDriverFactory`.
        timeout: Seconds to wait for elements.
    """

    def __init__(self, driver, timeout: float = 20) -> None:
        """Keep the driver and a reusable explicit wait."""
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

    def find(self, locator: Locator):
        """Wait until the element is visible and return it."""
        return self.wait.until(ec.visibility_of_element_located(locator))

    def find_all(self, locator: Locator) -> list:
        """All currently matching elements (no wait)."""
        return self.driver.find_elements(*locator)

    def tap(self, locator: Locator) -> None:
        """Wait until clickable, then tap."""
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
