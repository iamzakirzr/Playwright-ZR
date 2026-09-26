"""Browser-level UI: native dialogs, iframes and new tabs."""

import pytest
from playwright.sync_api import expect

from pages.playground import DialogsPage, FramesPage, TabsPage


class TestDialogs:
    """``alert``, ``confirm`` and ``prompt``; Playwright dismisses them unless a handler answers."""

    def test_alert_is_acknowledged(self, page, site, base_url_playground):
        """The alert's text can be asserted; accepting it lets the page continue."""
        dialogs = DialogsPage(page, base_url_playground).open()

        assert dialogs.click_and_answer("Alert", accept=True) == "Saved!"
        expect(dialogs.result).to_have_text("alert closed")

    @pytest.mark.parametrize(("accept", "outcome"), [(True, "deleted"), (False, "kept")])
    def test_confirm_accept_or_dismiss(self, page, site, base_url_playground, accept, outcome):
        """OK and Cancel lead to different outcomes."""
        dialogs = DialogsPage(page, base_url_playground).open()

        assert dialogs.click_and_answer("Confirm", accept=accept) == "Delete item?"
        expect(dialogs.result).to_have_text(outcome)

    def test_prompt_receives_typed_text(self, page, site, base_url_playground):
        """Text passed to ``accept`` is what the user "typed"."""
        dialogs = DialogsPage(page, base_url_playground).open()

        dialogs.click_and_answer("Prompt", accept=True, text="Ada")

        expect(dialogs.result).to_have_text("hello Ada")

    def test_prompt_cancelled(self, page, site, base_url_playground):
        """Dismissing a prompt returns null to the page."""
        dialogs = DialogsPage(page, base_url_playground).open()

        dialogs.click_and_answer("Prompt", accept=False)

        expect(dialogs.result).to_have_text("cancelled")


def test_payment_inside_an_iframe(page, site, base_url_playground):
    """``frame_locator`` reaches into the iframe; the parent page sees the result."""
    checkout = FramesPage(page, base_url_playground).open()

    checkout.pay("4111111111111111")

    expect(checkout.paid).to_have_text("Paid with card ending 1111")


def test_link_opens_in_a_new_tab(page, site, base_url_playground):
    """The new tab is a separate ``Page``; the original stays where it was."""
    tabs = TabsPage(page, base_url_playground).open()

    terms = tabs.open_terms()

    expect(terms).to_have_title("Terms")
    expect(terms.get_by_role("heading")).to_have_text("Terms and conditions")
    assert page.url.endswith("/tabs.html")
    assert len(page.context.pages) == 2
