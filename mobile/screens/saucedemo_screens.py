"""Screens for saucedemo.com in Chrome on Android (mobile web through Appium).

The selectors are the same ``data-test`` attributes the Playwright page objects
use. Only the driver differs, which is the point: one app, verified on a real
mobile browser engine and device.
"""

from __future__ import annotations

from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from mobile.screens.base_screen import BaseScreen, css
from reporting import step

#: A cold emulator's first navigation (DNS, TLS, JS bundle) is far slower than later element waits.
FIRST_LOAD_TIMEOUT_S = 60


class MobileLoginScreen(BaseScreen):
    """Login form in mobile Chrome."""

    USERNAME = css("[data-test='username']")
    PASSWORD = css("[data-test='password']")
    LOGIN = css("[data-test='login-button']")
    ERROR = css("[data-test='error']")

    @step("Open {url}")
    def open(self, url: str) -> MobileLoginScreen:
        """Navigate the device browser to ``url`` and wait for the form."""
        self.driver.get(url)
        WebDriverWait(self.driver, FIRST_LOAD_TIMEOUT_S).until(ec.visibility_of_element_located(self.LOGIN))
        return self

    @step("Log in as {username} (mobile)")
    def login_as(self, username: str, password: str) -> None:
        """Type credentials with the on-device keyboard and tap Login."""
        self.type(self.USERNAME, username)
        self.type(self.PASSWORD, password)
        self.tap(self.LOGIN)

    def error_text(self) -> str:
        """The validation banner text."""
        return self.find(self.ERROR).text


class MobileInventoryScreen(BaseScreen):
    """Product list in mobile Chrome."""

    TITLE = css("[data-test='title']")
    ITEMS = css("[data-test='inventory-item']")
    MENU = css("#react-burger-menu-btn")
    LOGOUT = css("[data-test='logout-sidebar-link']")

    def wait_loaded(self) -> MobileInventoryScreen:
        """Wait for the 'Products' title."""
        self.find(self.TITLE)
        return self

    def item_count(self) -> int:
        """Number of product cards."""
        return len(self.find_all(self.ITEMS))

    @step("Open the burger menu (mobile)")
    def open_menu(self) -> None:
        """Tap the burger menu."""
        self.tap(self.MENU)
