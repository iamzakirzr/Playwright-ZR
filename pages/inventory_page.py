"""Page object for the product list shown after login."""

from playwright.sync_api import expect

from pages.base_page import BasePage
from pages.components.header import Header
from reporting import step


class InventoryPage(BasePage):
    """Product grid with sorting and add-to-cart buttons."""

    path = "/inventory.html"

    def __init__(self, page, base_url):
        """Bind product-grid locators and the shared header."""
        super().__init__(page, base_url)
        self.header = Header(page)
        self.title = self.by_test_id("title")
        self.items = self.by_test_id("inventory-item")
        self.item_names = self.by_test_id("inventory-item-name")
        self.item_prices = self.by_test_id("inventory-item-price")
        self.sort_select = self.by_test_id("product-sort-container")

    def expect_loaded(self):
        """The page title reads 'Products'."""
        expect(self.title).to_have_text("Products")
        return self

    def item_count(self) -> int:
        """Number of product cards on the page."""
        return self.items.count()

    def names(self) -> list[str]:
        """Product names in display order."""
        return self.item_names.all_inner_texts()

    def prices(self) -> list[float]:
        """Product prices in display order, parsed from '$29.99' to 29.99."""
        return [float(p.replace("$", "")) for p in self.item_prices.all_inner_texts()]

    @step("Sort products by {option_value}")
    def sort_by(self, option_value: str) -> None:
        """Choose a sort order: ``az``, ``za``, ``lohi`` (price low to high) or ``hilo``."""
        self.sort_select.select_option(option_value)

    @step("Add '{product_name}' to cart")
    def add_to_cart(self, product_name: str) -> None:
        """Click 'Add to cart' on the card whose text contains ``product_name``."""
        item = self.items.filter(has_text=product_name)
        item.get_by_role("button", name="Add to cart").click()
