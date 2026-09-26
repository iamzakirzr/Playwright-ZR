"""Page object for the chat widget (``ai/chat_ui/index.html``)."""
from __future__ import annotations

from playwright.sync_api import expect

from pages.base_page import BasePage


class ChatPage(BasePage):
    """Chat widget: a message list, an input, a send button, a typing indicator and an error banner."""

    path = "/"

    def __init__(self, page, base_url):
        """Bind locators. Uses Playwright's standard ``data-testid`` attribute."""
        super().__init__(page, base_url)
        self.messages = page.get_by_test_id("messages")
        self.input = page.get_by_test_id("chat-input")
        self.send_button = page.get_by_test_id("send")
        self.typing = page.get_by_test_id("typing")
        self.error = page.get_by_test_id("error")
        self.bot_bubbles = self.messages.locator("[data-role=bot]")
        self.user_bubbles = self.messages.locator("[data-role=user]")

    def expect_loaded(self):
        """The input is visible and enabled."""
        expect(self.input).to_be_enabled()
        return self

    def configure(self, *, system: str, model: str) -> None:
        """Set the system prompt and model the widget sends (test hook on ``window.chatConfig``)."""
        self.page.evaluate("cfg => Object.assign(window.chatConfig, cfg)", {"system": system, "model": model})

    def type_message(self, text: str) -> None:
        """Type into the input without sending."""
        self.input.fill(text)

    def send(self, text: str) -> None:
        """Type ``text`` and press Enter."""
        self.type_message(text)
        self.input.press("Enter")

    def send_and_wait(self, text: str, timeout_ms: float = 180_000) -> str:
        """Send ``text`` and wait for a new bot bubble *or* the error banner; return the reply text.

        Waiting on either outcome with ``Locator.or_`` makes a backend failure
        fail fast with the banner text, instead of hanging until the timeout.

        Raises:
            AssertionError: If the error banner appears, or nothing appears within ``timeout_ms``.
        """
        before = self.bot_bubbles.count()
        self.send(text)
        new_reply = self.bot_bubbles.nth(before)
        expect(new_reply.or_(self.error.filter(visible=True))).to_be_visible(timeout=timeout_ms)
        if self.error.is_visible():
            raise AssertionError(f"Chat widget showed an error instead of a reply: {self.error.inner_text()!r}")
        return new_reply.inner_text()

    def transcript(self) -> list[tuple[str, str]]:
        """Every bubble as ``(role, text)``, in display order."""
        bubbles = self.messages.locator("li")
        return [(b.get_attribute("data-role"), b.inner_text()) for b in bubbles.all()]
