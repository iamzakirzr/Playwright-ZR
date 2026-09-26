"""Page objects for the Playwright playground (``tests/ui/essentials/site``).

One small class per page, each wrapping one Playwright technique behind an intention-revealing
method, so tests read as behaviour ("pay with card …") and the technique lives in one place:

| Page | Technique |
|---|---|
| :class:`ProductsPage` | network mocking (the page fetches ``/api/products``) |
| :class:`DialogsPage` | ``alert`` / ``confirm`` / ``prompt`` handling |
| :class:`FramesPage` | ``frame_locator`` for iframes |
| :class:`TabsPage` | new tabs via ``context.expect_page`` |
| :class:`FilesPage` | ``set_input_files`` uploads and ``expect_download`` |
| :class:`PlaygroundLoginPage` / :class:`AccountPage` | auth state reuse (``storage_state``) |
| :class:`EmulationPage` | locale, timezone, colour scheme, geolocation, offline |
| :class:`InteractionsPage` | hover, drag and drop, keyboard shortcuts |
"""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import Download, Page, expect

from pages.base_page import BasePage
from reporting import step


class PlaygroundPage(BasePage):
    """Base for playground pages: they use Playwright's default ``data-testid`` attribute."""

    def by_test_id(self, test_id: str):
        """Locate by ``data-testid`` (the playground's convention, unlike Sauce Demo's ``data-test``)."""
        return self.page.get_by_test_id(test_id)


class ProductsPage(PlaygroundPage):
    """Lists products fetched from ``GET /api/products``."""

    path = "/products.html"

    def __init__(self, page: Page, base_url: str) -> None:
        """Bind the status line and the product list."""
        super().__init__(page, base_url)
        self.status = self.by_test_id("status")
        self.items = self.by_test_id("product")
        self.banner = self.by_test_id("banner")

    def expect_loaded(self) -> ProductsPage:
        """The fetch finished (status no longer says Loading)."""
        expect(self.status).not_to_have_text("Loading…")
        return self

    def names(self) -> list[str]:
        """Rendered product lines, e.g. ``"Backpack - $29.99"``."""
        return self.items.all_inner_texts()


class DialogsPage(PlaygroundPage):
    """Buttons that open native browser dialogs."""

    path = "/dialogs.html"

    def __init__(self, page: Page, base_url: str) -> None:
        """Bind the result line."""
        super().__init__(page, base_url)
        self.result = self.by_test_id("result")

    @step("Click {button} and answer the dialog")
    def click_and_answer(self, button: str, accept: bool, text: str | None = None) -> str:
        """Click ``button``, accept or dismiss the dialog it opens (typing ``text`` into a prompt), return its message.

        Playwright auto-dismisses dialogs unless a handler is registered, so the handler is
        registered *before* the click, and only for this one dialog.
        """
        seen: list[str] = []

        def answer(dialog) -> None:
            seen.append(dialog.message)
            if not accept:
                dialog.dismiss()
            elif text is None:
                dialog.accept()
            else:
                dialog.accept(text)

        self.page.once("dialog", answer)
        self.page.get_by_role("button", name=button).click()
        return seen[0]


class FramesPage(PlaygroundPage):
    """Checkout page with the card form inside an iframe."""

    path = "/frames.html"

    def __init__(self, page: Page, base_url: str) -> None:
        """Bind the payment iframe and the confirmation line."""
        super().__init__(page, base_url)
        self.payment = page.frame_locator("iframe[title='Payment']")
        self.paid = self.by_test_id("paid")

    @step("Pay with card {card}")
    def pay(self, card: str) -> None:
        """Fill the card field and press Pay, both inside the iframe."""
        self.payment.locator("[name=card]").fill(card)
        self.payment.get_by_role("button", name="Pay").click()


class TabsPage(PlaygroundPage):
    """A link that opens in a new tab."""

    path = "/tabs.html"

    @step("Open the terms in a new tab")
    def open_terms(self) -> Page:
        """Click the link and return the new tab once it has loaded."""
        with self.page.context.expect_page() as new_tab:
            self.page.get_by_role("link", name="Terms and conditions").click()
        tab = new_tab.value
        tab.wait_for_load_state()
        return tab


class FilesPage(PlaygroundPage):
    """File upload input and a download link."""

    path = "/files.html"

    def __init__(self, page: Page, base_url: str) -> None:
        """Bind the upload input and the list of uploaded files."""
        super().__init__(page, base_url)
        self.upload_input = self.by_test_id("upload")
        self.uploaded = self.by_test_id("uploaded").locator("li")

    @step("Upload files")
    def upload(self, *files: Path | dict) -> None:
        """Attach files: paths on disk, or in-memory ``{"name", "mimeType", "buffer"}`` dicts."""
        self.upload_input.set_input_files(list(files))

    @step("Download the orders CSV")
    def download_orders(self) -> Download:
        """Click the download link and return Playwright's ``Download`` handle."""
        with self.page.expect_download() as download:
            self.page.get_by_role("button", name="Download orders").click()
        return download.value


class PlaygroundLoginPage(PlaygroundPage):
    """Username form; signing in stores a token in localStorage and a session cookie."""

    path = "/login.html"

    @step("Sign in to the playground as {username}")
    def sign_in(self, username: str) -> AccountPage:
        """Submit the form and wait for the account page."""
        self.page.get_by_label("Username").fill(username)
        self.page.get_by_role("button", name="Sign in").click()
        self.page.wait_for_url("**/account.html")
        return AccountPage(self.page, self.base_url)


class AccountPage(PlaygroundPage):
    """Greets a signed-in user; needs both the cookie and the localStorage token."""

    path = "/account.html"

    def __init__(self, page: Page, base_url: str) -> None:
        """Bind the greeting."""
        super().__init__(page, base_url)
        self.greeting = self.by_test_id("greeting")


class EmulationPage(PlaygroundPage):
    """Shows what the browser reports about locale, timezone, theme, network and position."""

    path = "/emulation.html"

    def value(self, test_id: str) -> str:
        """Text of one readout: ``locale``, ``timezone``, ``theme``, ``network`` or ``position``."""
        return self.by_test_id(test_id).inner_text()

    @step("Ask the browser for its location")
    def locate(self) -> str:
        """Press "Locate me" and return the reported ``lat,long`` (or ``denied``)."""
        self.page.get_by_role("button", name="Locate me").click()
        position = self.by_test_id("position")
        expect(position).not_to_be_empty()
        return position.inner_text()


class InteractionsPage(PlaygroundPage):
    """Hover tooltip, drag-and-drop cart and a Ctrl+K shortcut."""

    path = "/interactions.html"

    def __init__(self, page: Page, base_url: str) -> None:
        """Bind the tooltip, draggable item and drop zone."""
        super().__init__(page, base_url)
        self.tooltip = page.get_by_role("tooltip")
        self.item = self.by_test_id("item")
        self.cart_zone = self.by_test_id("cart-zone")
        self.search = self.by_test_id("search")

    def hover_help(self) -> None:
        """Hover the "What is CVV?" hint."""
        self.page.get_by_text("What is CVV?").hover()

    @step("Drag the backpack into the cart")
    def drag_item_to_cart(self) -> None:
        """Native HTML5 drag and drop, driven by Playwright's ``drag_to``."""
        self.item.drag_to(self.cart_zone)

    def press_search_shortcut(self) -> None:
        """Press Ctrl+K (Meta+K on macOS pages would use ``Meta``)."""
        self.page.keyboard.press("Control+k")
