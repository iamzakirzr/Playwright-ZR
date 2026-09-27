"""End-to-end purchase flow and inventory behaviour through page objects."""

import pytest
from playwright.sync_api import expect

from data import CheckoutCustomerFactory


@pytest.fixture
def browser_context_args(browser_context_args, sauce_auth_state):
    """Every test in this module starts signed in: log in once, reuse the saved session."""
    return {**browser_context_args, "storage_state": sauce_auth_state}


PRODUCTS = ["Sauce Labs Backpack", "Sauce Labs Bike Light"]


@pytest.mark.smoke
def test_end_to_end_purchase(signed_in, cart_page, checkout_page):
    """Add two products, check out, verify total = subtotal + tax, and see the confirmation."""
    for product in PRODUCTS:
        signed_in.add_to_cart(product)
    assert signed_in.header.cart_count() == len(PRODUCTS)

    signed_in.header.open_cart()
    cart_page.expect_loaded()
    assert sorted(cart_page.names()) == sorted(PRODUCTS)

    cart_page.checkout()
    checkout_page.expect_loaded()
    checkout_page.fill_customer_info(**CheckoutCustomerFactory.build())

    # Business rule: total = item total + tax (to the cent)
    assert checkout_page.item_total() == pytest.approx(29.99 + 9.99)
    assert checkout_page.total() == pytest.approx(checkout_page.item_total() + checkout_page.tax(), abs=0.01)

    checkout_page.finish()
    expect(checkout_page.complete_header).to_have_text("Thank you for your order!")


def test_checkout_requires_customer_info(signed_in, cart_page, checkout_page):
    """Checkout blocks an empty customer form with a validation error."""
    signed_in.add_to_cart(PRODUCTS[0])
    signed_in.header.open_cart()
    cart_page.checkout()

    checkout_page.fill_customer_info("", "", "")

    expect(checkout_page.error_message).to_contain_text("First Name is required")


@pytest.mark.parametrize(
    ("option", "key", "reverse"),
    [("lohi", "prices", False), ("hilo", "prices", True), ("az", "names", False), ("za", "names", True)],
)
def test_inventory_sorting(signed_in, option, key, reverse):
    """Each sort option orders the products correctly."""
    signed_in.sort_by(option)

    values = getattr(signed_in, key)()
    assert values == sorted(values, reverse=reverse)
