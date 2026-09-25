"""Reusable header component shared by all authenticated pages."""
from playwright.sync_api import Page


class Header:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.cart_link = page.locator("[data-test='shopping-cart-link']")
        self.cart_badge = page.locator("[data-test='shopping-cart-badge']")
        self.menu_button = page.get_by_role("button", name="Open Menu")
        self.logout_link = page.locator("[data-test='logout-sidebar-link']")

    def cart_count(self) -> int:
        return int(self.cart_badge.inner_text()) if self.cart_badge.is_visible() else 0

    def open_cart(self) -> None:
        self.cart_link.click()

    def logout(self) -> None:
        self.menu_button.click()
        self.logout_link.click()
