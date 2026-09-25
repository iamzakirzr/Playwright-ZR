from playwright.sync_api import expect

from pages.base_page import BasePage
from pages.components.header import Header


class CartPage(BasePage):
    path = "/cart.html"

    def __init__(self, page, base_url):
        super().__init__(page, base_url)
        self.header = Header(page)
        self.title = self.by_test_id("title")
        self.item_names = self.by_test_id("inventory-item-name")
        self.checkout_button = self.by_test_id("checkout")

    def expect_loaded(self):
        expect(self.title).to_have_text("Your Cart")
        return self

    def names(self) -> list[str]:
        return self.item_names.all_inner_texts()

    def checkout(self) -> None:
        self.checkout_button.click()
