"""Appium driver factory: builds sessions from settings (Factory pattern).

Two session types:

* **Mobile Chrome** (``create_chrome``): a real Android browser on a device or
  emulator, driven through Appium's UiAutomator2 driver. Locators are CSS, so the
  same ``data-test`` selectors as the web suite work.
* **Native app** (``create_native``): an installed APK. Locators are accessibility
  ids or resource ids, discovered with Appium Inspector.

Tests skip (never fail) when no Appium server answers, via :func:`appium_is_running`.
"""

from __future__ import annotations

import httpx
from appium import webdriver
from appium.options.android import UiAutomator2Options

from config import Settings


def appium_is_running(server_url: str, timeout: float = 3.0) -> bool:
    """True if an Appium 2 server answers ``GET /status`` with ``ready``."""
    try:
        response = httpx.get(f"{server_url.rstrip('/')}/status", timeout=timeout)
        return response.status_code == 200 and response.json().get("value", {}).get("ready", False)
    except (httpx.HTTPError, ValueError):
        return False


class AppiumDriverFactory:
    """Creates Appium sessions configured from :class:`~config.Settings`.

    Args:
        settings: Framework settings (Appium URL, device name, app path).
    """

    def __init__(self, settings: Settings) -> None:
        """Keep the settings; no session is opened until a ``create_*`` call."""
        self.settings = settings

    def _base_options(self) -> UiAutomator2Options:
        """Capabilities shared by every Android session."""
        options = UiAutomator2Options()
        options.device_name = self.settings.android_device_name
        options.new_command_timeout = 300
        options.set_capability("appium:adbExecTimeout", 60_000)
        return options

    def chrome_options(self) -> UiAutomator2Options:
        """Capabilities for Chrome on Android (chromedriver auto-downloaded to match Chrome's version)."""
        options = self._base_options()
        options.browser_name = "Chrome"
        options.set_capability("appium:chromedriverAutodownload", True)
        options.set_capability("goog:chromeOptions", {"args": ["--disable-fre", "--no-first-run", "--no-default-browser-check"]})
        return options

    def native_options(self, app_path: str) -> UiAutomator2Options:
        """Capabilities for installing and launching a native APK."""
        options = self._base_options()
        options.app = app_path
        options.auto_grant_permissions = True
        return options

    def create_chrome(self) -> webdriver.Remote:
        """Open a mobile Chrome session."""
        return webdriver.Remote(self.settings.appium_server_url, options=self.chrome_options())

    def create_native(self, app_path: str) -> webdriver.Remote:
        """Install ``app_path`` and open a native-app session."""
        return webdriver.Remote(self.settings.appium_server_url, options=self.native_options(app_path))
