"""Page object for the shopping cart."""

from playwright.sync_api import expect

from pages.base_page import BasePage
from pages.components.header import Header
from reporting import step


class CartPage(BasePage):
    """Cart line items and the checkout button."""

    path = "/cart.html"

    def __init__(self, page, base_url):
        """Bind cart locators and the shared header."""
        super().__init__(page, base_url)
        self.header = Header(page)
        self.title = self.by_test_id("title")
        self.item_names = self.by_test_id("inventory-item-name")
        self.checkout_button = self.by_test_id("checkout")

    def expect_loaded(self):
        """The page title reads 'Your Cart'."""
        expect(self.title).to_have_text("Your Cart")
        return self

    def names(self) -> list[str]:
        """Names of the products in the cart."""
        return self.item_names.all_inner_texts()

    @step("Start checkout")
    def checkout(self) -> None:
        """Start checkout."""
        self.checkout_button.click()
