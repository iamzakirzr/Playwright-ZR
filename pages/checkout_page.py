"""Checkout is three steps on Sauce Demo; modelled as one page object with step methods."""
from playwright.sync_api import expect

from pages.base_page import BasePage


class CheckoutPage(BasePage):
    path = "/checkout-step-one.html"

    def __init__(self, page, base_url):
        super().__init__(page, base_url)
        self.title = self.by_test_id("title")
        # step one
        self.first_name = self.by_test_id("firstName")
        self.last_name = self.by_test_id("lastName")
        self.postal_code = self.by_test_id("postalCode")
        self.continue_button = self.by_test_id("continue")
        self.error_message = self.by_test_id("error")
        # step two
        self.item_total_label = self.by_test_id("subtotal-label")
        self.tax_label = self.by_test_id("tax-label")
        self.total_label = self.by_test_id("total-label")
        self.finish_button = self.by_test_id("finish")
        # complete
        self.complete_header = self.by_test_id("complete-header")

    def expect_loaded(self):
        expect(self.title).to_have_text("Checkout: Your Information")
        return self

    def fill_customer_info(self, first: str, last: str, postal: str) -> None:
        self.first_name.fill(first)
        self.last_name.fill(last)
        self.postal_code.fill(postal)
        self.continue_button.click()

    @staticmethod
    def _money(text: str) -> float:
        return float(text.split("$")[-1])

    def item_total(self) -> float:
        return self._money(self.item_total_label.inner_text())

    def tax(self) -> float:
        return self._money(self.tax_label.inner_text())

    def total(self) -> float:
        return self._money(self.total_label.inner_text())

    def finish(self) -> None:
        self.finish_button.click()
