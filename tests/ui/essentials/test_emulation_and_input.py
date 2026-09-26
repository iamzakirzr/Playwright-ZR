"""Browser emulation (locale, timezone, theme, geolocation, offline) and rich input."""

import pytest
from playwright.sync_api import expect

from apps.playground import serve_playground
from pages.playground import EmulationPage, InteractionsPage


@pytest.fixture
def emulated(browser):
    """Factory: open the emulation page in a new context built with ``context_args``."""
    contexts = []

    def _open(**context_args) -> EmulationPage:
        context = browser.new_context(**context_args)
        contexts.append(context)
        site = serve_playground(context)
        return EmulationPage(context.new_page(), site.origin).open()

    yield _open
    for context in contexts:
        context.close()


def test_locale_changes_number_format(emulated):
    """German locale formats 1234.5 as 1.234,5."""
    assert emulated(locale="de-DE").value("locale") == "1.234,5"


def test_timezone_is_emulated(emulated):
    """Date logic sees the emulated timezone, whatever the CI machine uses."""
    assert emulated(timezone_id="Asia/Tokyo").value("timezone") == "Asia/Tokyo"


@pytest.mark.parametrize("scheme", ["dark", "light"])
def test_color_scheme(emulated, scheme):
    """``prefers-color-scheme`` follows the context option."""
    assert emulated(color_scheme=scheme).value("theme") == scheme


def test_geolocation_with_permission(emulated):
    """A granted permission plus a fixed position gives deterministic location features."""
    page = emulated(geolocation={"latitude": 35.68, "longitude": 139.69}, permissions=["geolocation"])

    assert page.locate() == "35.68,139.69"


def test_going_offline_is_noticed(emulated):
    """``set_offline`` flips ``navigator.onLine`` and fires the page's offline handler."""
    page = emulated()
    expect(page.by_test_id("network")).to_have_text("online")

    page.page.context.set_offline(True)

    expect(page.by_test_id("network")).to_have_text("offline")


class TestInput:
    """Hover, drag and drop, and keyboard shortcuts."""

    def test_hover_shows_tooltip(self, page, site, base_url_playground):
        """CSS :hover content only appears while the pointer is over the hint."""
        ui = InteractionsPage(page, base_url_playground).open()
        expect(ui.tooltip).to_be_hidden()

        ui.hover_help()

        expect(ui.tooltip).to_be_visible()

    def test_drag_and_drop(self, page, site, base_url_playground):
        """The dragged item ends up inside the drop zone."""
        ui = InteractionsPage(page, base_url_playground).open()

        ui.drag_item_to_cart()

        expect(ui.by_test_id("dropped")).to_have_text("Backpack in cart")
        expect(ui.cart_zone.get_by_test_id("item")).to_be_visible()

    def test_keyboard_shortcut_focuses_search(self, page, site, base_url_playground):
        """Ctrl+K moves focus to the search box."""
        ui = InteractionsPage(page, base_url_playground).open()

        ui.press_search_shortcut()

        expect(ui.search).to_be_focused()
