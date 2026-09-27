"""Uploads, downloads, and logging in once with ``storage_state``."""

import pytest
from playwright.sync_api import expect

from apps.playground import ORDERS_CSV, serve_playground
from pages.playground import AccountPage, FilesPage, PlaygroundLoginPage


class TestFiles:
    """``set_input_files`` and ``expect_download``."""

    def test_upload_a_file_from_disk(self, page, site, base_url_playground, tmp_path):
        """A real file is attached; the page sees its name and size."""
        receipt = tmp_path / "receipt.txt"
        receipt.write_text("total: 39.98")
        files = FilesPage(page, base_url_playground).open()

        files.upload(receipt)

        expect(files.uploaded).to_have_text(["receipt.txt (12 bytes)"])

    def test_upload_multiple_in_memory_files(self, page, site, base_url_playground):
        """Files can be built in memory: no temp files to clean up."""
        files = FilesPage(page, base_url_playground).open()

        files.upload(
            {"name": "a.csv", "mimeType": "text/csv", "buffer": b"x,y\n"},
            {"name": "b.csv", "mimeType": "text/csv", "buffer": b"1,2,3\n"},
        )

        expect(files.uploaded).to_have_text(["a.csv (4 bytes)", "b.csv (6 bytes)"])

    def test_download_has_the_expected_name_and_content(self, page, site, base_url_playground, tmp_path):
        """Downloads are saved by Playwright; check the suggested name and the bytes."""
        download = FilesPage(page, base_url_playground).open().download_orders()

        target = tmp_path / download.suggested_filename
        download.save_as(target)

        assert download.suggested_filename == "orders.csv"
        assert target.read_text() == ORDERS_CSV


class TestAuthState:
    """Log in once, save cookies + localStorage, start later tests already signed in."""

    @pytest.fixture
    def saved_state(self, page, site, base_url_playground, tmp_path):
        """Sign in through the UI once and save the storage state to a file."""
        account = PlaygroundLoginPage(page, base_url_playground).open().sign_in("ada")
        expect(account.greeting).to_have_text("Welcome back, ada")
        path = tmp_path / "state.json"
        page.context.storage_state(path=path)
        return path

    def test_saved_state_contains_cookie_and_token(self, saved_state):
        """The file holds both halves of the session."""
        state = saved_state.read_text()

        assert '"name": "session"' in state
        assert "tok-ada" in state

    def test_new_context_with_saved_state_skips_login(self, browser, saved_state, base_url_playground):
        """A fresh context seeded with the state lands on the account page signed in."""
        context = browser.new_context(storage_state=saved_state)
        try:
            serve_playground(context)
            page = context.new_page()
            expect(AccountPage(page, base_url_playground).open().greeting).to_have_text("Welcome back, ada")
        finally:
            context.close()

    def test_new_context_without_state_is_signed_out(self, browser, base_url_playground):
        """Contexts are isolated: no state means no session."""
        context = browser.new_context()
        try:
            serve_playground(context)
            page = context.new_page()
            expect(AccountPage(page, base_url_playground).open().greeting).to_have_text("Please sign in")
        finally:
            context.close()
