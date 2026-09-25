"""Header component shared by every authenticated page (composition over inheritance)."""
from playwright.sync_api import Page


class Header:
    """The top bar: cart link, cart badge and burger menu.

    Pages *have* a header rather than *being* one. That's composition, so the
    same component object is reused by the inventory, cart and checkout pages.

    Args:
        page: The Playwright page the header lives on.
    """

    def __init__(self, page: Page) -> None:
        """Bind the header's locators."""
        self.page = page
        self.cart_link = page.locator("[data-test='shopping-cart-link']")
        self.cart_badge = page.locator("[data-test='shopping-cart-badge']")
        self.menu_button = page.get_by_role("button", name="Open Menu")
        self.logout_link = page.locator("[data-test='logout-sidebar-link']")

    def cart_count(self) -> int:
        """Number shown on the cart badge (0 when the badge is hidden)."""
        return int(self.cart_badge.inner_text()) if self.cart_badge.is_visible() else 0

    def open_cart(self) -> None:
        """Click the cart icon."""
        self.cart_link.click()

    def logout(self) -> None:
        """Open the burger menu and log out."""
        self.menu_button.click()
        self.logout_link.click()
