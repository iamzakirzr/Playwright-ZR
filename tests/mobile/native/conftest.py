"""Appium fixtures. Every test here skips unless an Appium server is running with a device attached."""

from __future__ import annotations

import pytest

from mobile import AppiumDriverFactory, appium_is_running


@pytest.fixture(scope="session")
def appium_factory(settings) -> AppiumDriverFactory:
    """Driver factory; skips the session's native tests when Appium isn't reachable."""
    if not appium_is_running(settings.appium_server_url):
        pytest.skip(f"No Appium server at {settings.appium_server_url} (see docs/learning-path/10-mobile.md)")
    return AppiumDriverFactory(settings)


@pytest.fixture
def android_chrome(appium_factory):
    """A fresh Chrome-on-Android session per test, always closed afterwards."""
    driver = appium_factory.create_chrome()
    yield driver
    driver.quit()
