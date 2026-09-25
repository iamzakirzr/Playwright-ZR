"""Page object for Sauce Demo's three-step checkout (information, overview, complete)."""
from playwright.sync_api import expect

from pages.base_page import BasePage


class CheckoutPage(BasePage):
    """Checkout, modelled as one page object with one method per step."""

    path = "/checkout-step-one.html"

    def __init__(self, page, base_url):
        """Bind the locators for all three steps."""
        super().__init__(page, base_url)
        self.title = self.by_test_id("title")
        # step one: customer information
        self.first_name = self.by_test_id("firstName")
        self.last_name = self.by_test_id("lastName")
        self.postal_code = self.by_test_id("postalCode")
        self.continue_button = self.by_test_id("continue")
        self.error_message = self.by_test_id("error")
        # step two: overview
        self.item_total_label = self.by_test_id("subtotal-label")
        self.tax_label = self.by_test_id("tax-label")
        self.total_label = self.by_test_id("total-label")
        self.finish_button = self.by_test_id("finish")
        # step three: complete
        self.complete_header = self.by_test_id("complete-header")

    def expect_loaded(self):
        """Step one's title is shown."""
        expect(self.title).to_have_text("Checkout: Your Information")
        return self

    def fill_customer_info(self, first: str, last: str, postal: str) -> None:
        """Complete step one and continue to the overview."""
        self.first_name.fill(first)
        self.last_name.fill(last)
        self.postal_code.fill(postal)
        self.continue_button.click()

    @staticmethod
    def _money(text: str) -> float:
        """Parse the amount after the last '$' in a label such as 'Item total: $39.98'."""
        return float(text.split("$")[-1])

    def item_total(self) -> float:
        """Sum of item prices before tax."""
        return self._money(self.item_total_label.inner_text())

    def tax(self) -> float:
        """Tax amount."""
        return self._money(self.tax_label.inner_text())

    def total(self) -> float:
        """Grand total including tax."""
        return self._money(self.total_label.inner_text())

    def finish(self) -> None:
        """Place the order."""
        self.finish_button.click()
