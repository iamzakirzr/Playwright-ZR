"""Login page tests: success, locked account, validation messages, logout."""

import pytest
from playwright.sync_api import expect


@pytest.mark.smoke
def test_standard_user_can_log_in(login_page, inventory_page, settings):
    """A valid user lands on the inventory with all six products."""
    login_page.open().expect_loaded()
    login_page.login_as(settings.ui_standard_user, settings.ui_password)

    inventory_page.expect_loaded()
    assert inventory_page.item_count() == 6


def test_locked_out_user_sees_error(login_page, settings):
    """A locked account is refused with a clear message."""
    login_page.open().login_as(settings.ui_locked_user, settings.ui_password)

    expect(login_page.error_message).to_be_visible()
    assert "locked out" in login_page.error_text()


@pytest.mark.parametrize(
    "username, password, expected_error",
    [
        ("", "secret_sauce", "Username is required"),
        ("standard_user", "", "Password is required"),
        ("standard_user", "wrong", "do not match any user"),
    ],
    ids=["missing-username", "missing-password", "wrong-password"],
)
def test_login_validation(login_page, username, password, expected_error):
    """Missing or wrong credentials show the matching validation message."""
    login_page.open().login_as(username, password)

    assert expected_error in login_page.error_text()


def test_logout_returns_to_login(logged_in, login_page):
    """Logging out returns to the login page."""
    logged_in.header.logout()

    login_page.expect_loaded()
