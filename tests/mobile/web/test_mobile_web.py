"""Mobile-web tests: the same page objects, on phone-sized, touch-enabled devices.

What a mobile check should catch that a desktop check can't: layouts that
don't reflow, horizontal scrolling, controls that only work with a mouse, and
touch targets that are hidden off-screen.
"""

import pytest
from playwright.sync_api import expect

from ai.chat_ui import CHAT_ORIGIN, ChatHost
from pages import ChatPage

#: Every mobile page needs this; without it WebKit lays out at 980px and taps land on <html>.
MOBILE_VIEWPORT_META = '<meta name="viewport" content="width=device-width, initial-scale=1">'


def column_count(page, locator) -> int:
    """How many distinct x positions the first cards sit at (1 means a stacked, single-column layout)."""
    boxes = [locator.nth(i).bounding_box() for i in range(min(4, locator.count()))]
    return len({round(b["x"]) for b in boxes})


def has_horizontal_scroll(page) -> bool:
    """True when the document is wider than the viewport (a classic mobile layout bug)."""
    return page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1")


def test_device_profile_is_applied(mobile_page, playwright, device_name):
    """The emulated viewport, touch input and mobile user agent are active.

    Touch is checked by behaviour (a tap delivers a ``touchstart`` event), not by
    ``navigator.maxTouchPoints``: Playwright's Linux WebKit build reports 0 there
    even though touch events work.
    """
    expected = playwright.devices[device_name]

    assert mobile_page.viewport_size == expected["viewport"]
    mobile_page.set_content(f"{MOBILE_VIEWPORT_META}<body style='height:100vh'></body>")
    mobile_page.evaluate("window.touched = false; document.addEventListener('touchstart', () => window.touched = true)")
    mobile_page.tap("body")
    assert mobile_page.evaluate("window.touched"), "a tap did not deliver a touchstart event"
    assert mobile_page.evaluate("navigator.userAgent") == expected["user_agent"]


@pytest.mark.smoke
def test_login_works_on_phone(mobile_inventory):
    """The desktop login flow and page objects work unchanged on a phone."""
    assert mobile_inventory.item_count() == 6


def test_products_stack_in_one_column(mobile_inventory, mobile_page):
    """On a phone the product grid reflows to a single column."""
    assert column_count(mobile_page, mobile_inventory.items) == 1


def test_desktop_shows_multiple_columns(logged_in, page):
    """Control: the same check sees several columns on desktop, so the phone assertion is meaningful."""
    assert column_count(page, logged_in.items) > 1


def test_no_horizontal_scroll(mobile_inventory, mobile_page):
    """Nothing overflows the viewport sideways."""
    assert not has_horizontal_scroll(mobile_page)


def test_menu_opens_by_tap(mobile_inventory):
    """The burger menu responds to a touch tap, not only a mouse click."""
    mobile_inventory.header.menu_button.tap()

    expect(mobile_inventory.header.logout_link).to_be_visible()


def test_landscape_orientation(playwright, browser, settings):
    """Rotated to landscape, the page still fits without sideways scrolling."""
    from pages import InventoryPage, LoginPage

    context = browser.new_context(**playwright.devices["iPhone 13 landscape"])
    page = context.new_page()
    try:
        LoginPage(page, settings.ui_base_url).open().login_as(settings.ui_standard_user, settings.ui_password)
        InventoryPage(page, settings.ui_base_url).expect_loaded()
        assert not has_horizontal_scroll(page)
    finally:
        context.close()


def test_chat_widget_is_usable_on_phone(mobile_page, settings):
    """The AI chat widget: input on screen, tap to focus, reply rendered (stubbed backend)."""
    ChatHost(mobile_page, settings.ollama_host).install().use_stub(reply="Hi from mobile")
    chat = ChatPage(mobile_page, CHAT_ORIGIN).open().expect_loaded()

    # Without <meta name="viewport"> the page lays out at 980px and is scaled down to fit.
    assert mobile_page.evaluate("window.innerWidth") == mobile_page.viewport_size["width"], "missing viewport meta tag"
    expect(chat.input).to_be_in_viewport()
    chat.input.tap()
    assert chat.send_and_wait("hello") == "Hi from mobile"
