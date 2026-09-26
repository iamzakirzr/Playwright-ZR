"""Step definitions for the UI features (login, checkout).

Steps are thin: each one calls a page-object method. The Gherkin reads like a
specification; the page objects hold the automation. Fixtures (``login_page``,
``logged_in`` ...) are the same ones the plain pytest UI tests use.
"""

import pytest
from playwright.sync_api import expect
from pytest_bdd import given, parsers, scenarios, then, when

from data import CheckoutCustomerFactory

scenarios("login.feature", "shopping.feature")


@given("I am on the login page")
def on_login_page(login_page):
    """Open the login page."""
    login_page.open().expect_loaded()


@given(parsers.parse('I am signed in as "{username}"'))
def signed_in(login_page, inventory_page, settings, username):
    """Log in and land on the inventory."""
    login_page.open().login_as(username, settings.ui_password)
    inventory_page.expect_loaded()


@when(parsers.re(r'I log in as "(?P<username>[^"]*)" with password "(?P<password>[^"]*)"'))
def log_in_with_password(login_page, username, password):
    """Log in with explicit credentials (may be empty)."""
    login_page.login_as(username, password)


@when(parsers.re(r'I log in as "(?P<username>[^"]*)"$'))
def log_in(login_page, settings, username):
    """Log in with the configured password.

    A strict, end-anchored regex: with ``parsers.parse`` the ``{username}`` field
    would also swallow the longer 'with password ...' step and run the wrong code.
    """
    login_page.login_as(username, settings.ui_password)


@when(parsers.parse('I add "{product}" to the cart'))
def add_product(inventory_page, product):
    """Add a product from the inventory page."""
    inventory_page.add_to_cart(product)


@when("I check out with generated customer details")
def check_out(inventory_page, cart_page, checkout_page):
    """Go to the cart, start checkout and submit Faker-generated details."""
    inventory_page.header.open_cart()
    cart_page.checkout()
    checkout_page.fill_customer_info(**CheckoutCustomerFactory.build())


@then(parsers.parse("I see the product catalogue with {count:d} products"))
def see_catalogue(inventory_page, count):
    """The inventory shows the expected number of products."""
    inventory_page.expect_loaded()
    assert inventory_page.item_count() == count


@then(parsers.parse('I see the error "{error}"'))
def see_error(login_page, error):
    """The login error banner contains ``error``."""
    assert error in login_page.error_text()


@then("the order total equals the item total plus tax")
def total_is_consistent(checkout_page):
    """Business rule on the overview step."""
    assert checkout_page.total() == pytest.approx(checkout_page.item_total() + checkout_page.tax(), abs=0.01)


@then(parsers.parse('I see "{message}"'))
def see_confirmation(checkout_page, message):
    """Finish the order and see the confirmation header."""
    checkout_page.finish()
    expect(checkout_page.complete_header).to_have_text(message)
