from playwright.sync_api import expect

from pages.base_page import BasePage


class LoginPage(BasePage):
    path = "/"

    def __init__(self, page, base_url):
        super().__init__(page, base_url)
        self.username_input = self.by_test_id("username")
        self.password_input = self.by_test_id("password")
        self.login_button = self.by_test_id("login-button")
        self.error_message = self.by_test_id("error")

    def expect_loaded(self):
        expect(self.login_button).to_be_visible()
        return self

    def login_as(self, username: str, password: str) -> None:
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()

    def error_text(self) -> str:
        return self.error_message.inner_text()
