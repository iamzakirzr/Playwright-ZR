"""Page object for the Sauce Demo login screen."""

from playwright.sync_api import expect

from pages.base_page import BasePage
from reporting import step


class LoginPage(BasePage):
    """Username and password form plus its error banner."""

    path = "/"

    def __init__(self, page, base_url):
        """Bind the login form locators."""
        super().__init__(page, base_url)
        self.username_input = self.by_test_id("username")
        self.password_input = self.by_test_id("password")
        self.login_button = self.by_test_id("login-button")
        self.error_message = self.by_test_id("error")

    def expect_loaded(self):
        """The login button is visible."""
        expect(self.login_button).to_be_visible()
        return self

    @step("Log in as {username}")
    def login_as(self, username: str, password: str) -> None:
        """Fill both fields and submit."""
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()

    def error_text(self) -> str:
        """Text of the validation error banner."""
        return self.error_message.inner_text()
