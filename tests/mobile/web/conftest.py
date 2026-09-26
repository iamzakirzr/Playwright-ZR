"""Mobile-web fixtures: a browser context per device profile (viewport, user agent, touch, DPR).

Playwright's device descriptors emulate a phone's viewport, pixel ratio, touch
support and user agent. The *engine* stays whatever ``--browser`` selects:
iPhone profiles on Chromium emulate the screen, not Safari's WebKit. Run
``pytest --browser webkit -m mobile_web`` (as CI does) to use the real Safari engine.
"""

from __future__ import annotations

import pytest

from pages import InventoryPage, LoginPage

PHONES = ["Pixel 7", "iPhone 13"]


@pytest.fixture(params=PHONES)
def device_name(request) -> str:
    """Each test runs once per phone profile."""
    return request.param


@pytest.fixture
def mobile_page(playwright, browser, device_name):
    """A page in a fresh context configured as ``device_name``."""
    context = browser.new_context(**playwright.devices[device_name])
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture
def mobile_login(mobile_page, settings) -> LoginPage:
    """Login page object bound to the mobile page (same class as on desktop)."""
    return LoginPage(mobile_page, settings.ui_base_url)


@pytest.fixture
def mobile_inventory(mobile_login, mobile_page, settings) -> InventoryPage:
    """Signed-in inventory page on the phone."""
    mobile_login.open().login_as(settings.ui_standard_user, settings.ui_password)
    return InventoryPage(mobile_page, settings.ui_base_url).expect_loaded()
