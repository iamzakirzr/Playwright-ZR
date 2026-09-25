from playwright.sync_api import expect

from pages.base_page import BasePage
from pages.components.header import Header


class InventoryPage(BasePage):
    path = "/inventory.html"

    def __init__(self, page, base_url):
        super().__init__(page, base_url)
        self.header = Header(page)
        self.title = self.by_test_id("title")
        self.items = self.by_test_id("inventory-item")
        self.item_names = self.by_test_id("inventory-item-name")
        self.item_prices = self.by_test_id("inventory-item-price")
        self.sort_select = self.by_test_id("product-sort-container")

    def expect_loaded(self):
        expect(self.title).to_have_text("Products")
        return self

    def item_count(self) -> int:
        return self.items.count()

    def names(self) -> list[str]:
        return self.item_names.all_inner_texts()

    def prices(self) -> list[float]:
        return [float(p.replace("$", "")) for p in self.item_prices.all_inner_texts()]

    def sort_by(self, option_value: str) -> None:
        """option_value: az | za | lohi | hilo"""
        self.sort_select.select_option(option_value)

    def add_to_cart(self, product_name: str) -> None:
        item = self.items.filter(has_text=product_name)
        item.get_by_role("button", name="Add to cart").click()
