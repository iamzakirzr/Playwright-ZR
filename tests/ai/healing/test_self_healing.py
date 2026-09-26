"""Self-healing locators: offline tests with a fake healer, then a live test with a local LLM.

Scenario: the page object was written for v1 of a login page. A front-end
refactor (v2) renamed every id and data-test attribute. Without healing, every
test on the page breaks; with healing, the LLM maps each element to its new
selector, the fix is validated, cached, and logged for the page-object owner.
"""

import json

import pytest

from ai.chatbot import ScriptedChatbot
from pages.demo_login_page import DemoLoginPage
from pages.healing import HealingCache, LlmLocatorHealer, LocatorHealingError, SelfHealingLocator


class FakeHealer:
    """Returns fixed candidates per element description and counts calls (a spy)."""

    def __init__(self, answers: dict[str, list[str]]):
        """``answers`` maps an element description to the candidates to return."""
        self.answers = answers
        self.calls: list[str] = []

    def suggest(self, description, broken_selector, html):
        """Record the call and return the configured candidates."""
        self.calls.append(description)
        return self.answers.get(description, [])


V2_ANSWERS = {
    "the Username text input": ["[data-testid='signin-username']"],
    "the Password input": ["#login-secret"],
    "the Login submit button": ["button", "#does-not-exist", "[data-testid='signin-submit']"],
}


class TestResolution:
    """Resolution order: current, then cache, then healer."""

    def test_working_selector_never_calls_the_healer(self, page, healing_cache):
        """On v1 every selector works: zero healer calls, nothing cached."""
        healer = FakeHealer({})
        login = DemoLoginPage(page, healer, healing_cache).load("v1")

        login.login_as("ada", "secret")

        assert "Welcome, ada" in login.result_text()
        assert healer.calls == [] and len(healing_cache) == 0
        assert login.login_button.resolved_by == "current"

    def test_late_rendering_element_is_waited_for_not_healed(self, page, healing_cache):
        """Regression: count() doesn't wait, so an element rendered 300 ms after a click was
        "healed" by the LLM and a bogus fix was cached."""
        page.set_content(
            "<div id='root'></div><script>setTimeout(() => {"
            "document.getElementById('root').innerHTML = \"<button id='save'>Save</button>\"}, 300)</script>"
        )
        healer = FakeHealer({"the Save button": ["#root"]})
        save = SelfHealingLocator(page, "Demo.save", "#save", "the Save button", healer, healing_cache)

        save.resolve()

        assert save.resolved_by == "current"
        assert healer.calls == [] and len(healing_cache) == 0

    def test_broken_selectors_are_healed_and_the_flow_passes(self, page, healing_cache):
        """On v2 all three selectors break, are healed, and the login still succeeds."""
        login = DemoLoginPage(page, FakeHealer(V2_ANSWERS), healing_cache).load("v2")

        login.login_as("ada", "secret")

        assert "Welcome, ada" in login.result_text()
        assert login.login_button.resolved_by == "healed"
        assert len(healing_cache) == 3

    def test_ambiguous_and_missing_candidates_are_skipped(self, page, healing_cache):
        """``button`` matches two elements and ``#does-not-exist`` none; the third, unique candidate wins."""
        login = DemoLoginPage(page, FakeHealer(V2_ANSWERS), healing_cache).load("v2")

        login.login_button.resolve()

        assert healing_cache.get("DemoLoginPage.login_button").healed == "[data-testid='signin-submit']"

    def test_cache_is_reused_without_a_second_healer_call(self, page, tmp_path):
        """A healed selector persisted to disk is used by a new page object with no healer call."""
        path = tmp_path / "healed.json"
        DemoLoginPage(page, FakeHealer(V2_ANSWERS), HealingCache(path)).load("v2").login_button.resolve()

        second_healer = FakeHealer({})
        login = DemoLoginPage(page, second_healer, HealingCache(path)).load("v2")
        login.login_button.resolve()

        assert login.login_button.resolved_by == "cache"
        assert second_healer.calls == []

    def test_cache_file_records_what_changed(self, page, healing_cache):
        """The JSON cache is the page owner's to-do list: original, healed, URL and timestamp."""
        DemoLoginPage(page, FakeHealer(V2_ANSWERS), healing_cache).load("v2").login_button.resolve()

        entry = json.loads(healing_cache.path.read_text())["DemoLoginPage.login_button"]
        assert entry["original"] == "[data-test='login-button']"
        assert entry["healed"] == "[data-testid='signin-submit']"
        assert entry["url"].endswith("login_v2.html") and entry["healed_at"]

    def test_unhealable_element_fails_loudly(self, page, healing_cache):
        """If no candidate works, the test fails with a clear error; it never guesses."""
        login = DemoLoginPage(page, FakeHealer({"the Login submit button": ["#nope", "button"]}), healing_cache).load("v2")

        with pytest.raises(LocatorHealingError, match="login_button"):
            login.login_button.resolve()


class TestPageContext:
    """Context engineering: the healer sees interactive elements only, within a size budget."""

    def test_context_contains_interactive_elements_only(self, page, healing_cache):
        """Inputs, buttons and links are sent; headings are not."""
        login = DemoLoginPage(page, FakeHealer({}), healing_cache).load("v2")

        html = login.login_button.page_context()

        assert "signin-submit" in html and "login-secret" in html
        assert "<h1" not in html

    def test_context_respects_budget(self, page, healing_cache):
        """The HTML budget caps prompt size."""
        login = DemoLoginPage(page, FakeHealer({}), healing_cache).load("v2")
        login.login_button.max_html_chars = 200

        assert len(login.login_button.page_context()) <= 200


class TestLlmHealerParsing:
    """The LLM healer tolerates bad model output."""

    @pytest.mark.parametrize(
        ("reply", "expected"),
        [
            ('{"candidates": ["#a", "#b"]}', ["#a", "#b"]),
            ('{"candidates": ["#a", "", 3]}', ["#a"]),
            ("not json", []),
            ('["#a"]', []),
        ],
        ids=["valid", "junk-items", "not-json", "wrong-shape"],
    )
    def test_suggest_parses_candidates(self, reply, expected):
        """Only non-empty string selectors from a ``{"candidates": [...]}`` object are returned."""
        healer = LlmLocatorHealer(ScriptedChatbot([reply]))
        assert healer.suggest("x", "#old", "<button>") == expected


def test_live_llm_heals_the_v2_page(page, healing_cache, chatbot):
    """End to end with the local LLM: every v2 element heals and the login succeeds."""
    login = DemoLoginPage(page, LlmLocatorHealer(chatbot), healing_cache).load("v2")

    login.login_as("grace", "secret")

    assert "Welcome, grace" in login.result_text()
    assert {e.resolved_by for e in (login.username, login.password, login.login_button)} == {"healed"}
