"""Chat widget UI tests with Playwright network interception (stubbed backend: fast, offline).

The LLM is replaced with canned responses, so these tests check the *UI*
contract deterministically: rendering, request payload, loading state, error
handling, and safe rendering of untrusted model output.
"""
import time

import pytest
from playwright.sync_api import expect

from ai.chat_ui import ChatHost


def test_user_message_and_bot_reply_render_in_order(chat_host, chat_page):
    """User bubble first, then the bot's reply; the input is cleared after sending."""
    chat_host.use_stub(reply="You have 45 days to return an item.")

    reply = chat_page.send_and_wait("How long is the return window?")

    assert reply == "You have 45 days to return an item."
    assert chat_page.transcript() == [
        ("user", "How long is the return window?"),
        ("bot", "You have 45 days to return an item."),
    ]
    expect(chat_page.input).to_have_value("")


def test_request_payload_contract(chat_host, chat_page):
    """The widget sends the configured model, the system prompt, the user text, and stream=false."""
    chat_host.use_stub()
    chat_page.configure(system="SYSTEM-UNDER-TEST", model="test-model")

    chat_page.send_and_wait("hello")

    body = chat_host.last_request
    assert body["model"] == "test-model"
    assert body["stream"] is False
    assert body["messages"] == [
        {"role": "system", "content": "SYSTEM-UNDER-TEST"},
        {"role": "user", "content": "hello"},
    ]


def test_loading_state_while_model_is_thinking(chat_host, chat_page):
    """While the request is pending: typing indicator shown, input and button disabled."""
    chat_host.use_hold()
    chat_page.send("slow question")

    expect(chat_page.typing).to_be_visible()
    expect(chat_page.input).to_be_disabled()
    expect(chat_page.send_button).to_be_disabled()

    chat_host.release("done")
    expect(chat_page.bot_bubbles.last).to_have_text("done")
    expect(chat_page.typing).to_be_hidden()
    expect(chat_page.input).to_be_enabled()


def test_backend_error_shows_friendly_message(chat_host, chat_page):
    """A 500 from the model backend shows a friendly error and no bot bubble."""
    chat_host.use_stub(status=500)

    chat_page.send("anything")

    expect(chat_page.error).to_have_text("Sorry, something went wrong. Please try again.")
    expect(chat_page.bot_bubbles).to_have_count(0)
    expect(chat_page.input).to_be_enabled()


def test_model_output_is_rendered_as_text_not_html(chat_host, chat_page, page):
    """XSS guard: HTML in a model reply is displayed literally and never executed."""
    payload = '<img src=x onerror="window.__xss=1"><b>bold</b>'
    chat_host.use_stub(reply=payload)

    chat_page.send_and_wait("show me html")

    expect(chat_page.bot_bubbles.last).to_have_text(payload)
    expect(chat_page.messages.locator("img, b")).to_have_count(0)
    assert page.evaluate("window.__xss") is None


def test_blank_message_is_not_sent(chat_host, chat_page):
    """Whitespace-only input sends no request and adds no bubble."""
    chat_host.use_stub()

    chat_page.send("   ")

    expect(chat_page.user_bubbles).to_have_count(0)
    assert chat_host.requests == []


def test_send_and_wait_fails_fast_on_backend_error(chat_host, chat_page):
    """The page object surfaces the error banner immediately instead of waiting out the timeout."""
    chat_host.use_stub(status=403)
    started = time.perf_counter()

    with pytest.raises(AssertionError, match="error instead of a reply"):
        chat_page.send_and_wait("hello", timeout_ms=30_000)
    assert time.perf_counter() - started < 10


def test_proxy_strips_browser_only_headers():
    """Proxy mode must not forward Origin: Ollama rejects unknown origins with 403.

    Tested as a pure function because ``route.fetch`` goes through Playwright's
    HTTP client, which page and context routes can't intercept.
    """
    browser_headers = {"Origin": "http://chatbot.local", "Referer": "http://chatbot.local/", "Content-Type": "application/json"}

    assert ChatHost.forward_headers(browser_headers) == {"Content-Type": "application/json"}
