"""Real-device mobile tests through Appium: saucedemo in Chrome on an Android emulator.

These need an Appium 2 server, the UiAutomator2 driver and an Android device or
emulator, so they run in the CI ``mobile-native`` job and skip everywhere else.
The offline tests below check the capability wiring without any device.
"""

import pytest

from mobile import AppiumDriverFactory, appium_is_running
from mobile.screens import MobileInventoryScreen, MobileLoginScreen


class TestCapabilities:
    """Offline: the factory builds the capabilities Appium expects."""

    def test_chrome_capabilities(self, settings):
        """Chrome session: UiAutomator2, the Chrome browser, chromedriver auto-download."""
        caps = AppiumDriverFactory(settings).chrome_options().to_capabilities()

        assert caps["platformName"] == "Android"
        assert caps["automationName"] == "UIAutomator2"
        assert caps["browserName"] == "Chrome"
        assert caps["appium:chromedriverAutodownload"] is True
        assert caps["appium:deviceName"] == settings.android_device_name

    def test_native_capabilities(self, settings):
        """Native session: the APK path is set and runtime permissions are auto-granted."""
        caps = AppiumDriverFactory(settings).native_options("/tmp/app.apk").to_capabilities()

        assert caps["appium:app"] == "/tmp/app.apk"
        assert caps["appium:autoGrantPermissions"] is True
        assert "browserName" not in caps

    def test_unreachable_server_is_detected(self):
        """The skip guard reports False instead of raising when nothing listens."""
        assert appium_is_running("http://127.0.0.1:9", timeout=0.5) is False


@pytest.mark.smoke
def test_login_on_android_chrome(android_chrome, settings):
    """Log in with the on-device keyboard; all six products load in mobile Chrome."""
    MobileLoginScreen(android_chrome).open(settings.ui_base_url).login_as(settings.ui_standard_user, settings.ui_password)

    assert MobileInventoryScreen(android_chrome).wait_loaded().item_count() == 6


def test_locked_user_error_on_android(android_chrome, settings):
    """Validation messages render on the device."""
    login = MobileLoginScreen(android_chrome).open(settings.ui_base_url)
    login.login_as(settings.ui_locked_user, settings.ui_password)

    assert "locked out" in login.error_text()


def test_menu_by_tap_and_rotation(android_chrome, settings):
    """The burger menu opens by tap, in both portrait and landscape."""
    MobileLoginScreen(android_chrome).open(settings.ui_base_url).login_as(settings.ui_standard_user, settings.ui_password)
    inventory = MobileInventoryScreen(android_chrome).wait_loaded()

    inventory.rotate("LANDSCAPE")
    try:
        inventory.open_menu()
        assert inventory.is_visible(MobileInventoryScreen.LOGOUT)
    finally:
        inventory.rotate("PORTRAIT")
