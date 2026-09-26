"""Step definitions for the AI assistant feature (``tests/bdd/features/ai_assistant.feature``).

Lives next to the agent fixtures (``assistant``, ``session_id`` in this folder's
conftest) rather than in ``tests/bdd``. Importing a conftest as a plugin from
another folder breaks full-tree collection ("Plugin already registered").
"""

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

# pytest-bdd requests fixtures inside steps, so collection-time auto-marking
# can't see the Ollama dependency; mark it explicitly or CI would skip it silently.
pytestmark = [pytest.mark.bdd, pytest.mark.live]

scenarios("ai_assistant.feature")


@given("a new chat session", target_fixture="chat")
def new_session(session_id):
    """A dict holding this scenario's session id and the latest reply."""
    return {"session": session_id, "reply": None}


@when(parsers.parse('I say "{message}"'))
def say(assistant, chat, message):
    """Send a chat message and remember the reply."""
    chat["reply"] = assistant.chat(chat["session"], message)


@then(parsers.parse('my cart contains {quantity:d} x "{product}"'))
def cart_contains(assistant, chat, quantity, product):
    """State oracle: the cart API, not the chat text."""
    assert assistant.quantity_of(chat["session"], product) == quantity, assistant.cart(chat["session"])


@then(parsers.parse('the assistant called the "{tool}" tool'))
def called_tool(chat, tool):
    """Trajectory oracle: the tool actually ran."""
    assert tool in [c["name"] for c in chat["reply"]["tools_called"]], chat["reply"]


@then(parsers.parse('the reply mentions "{text}"'))
def reply_mentions(chat, text):
    """The reply text contains ``text``."""
    assert text in chat["reply"]["reply"], chat["reply"]


@then("my cart is empty")
def cart_is_empty(assistant, chat):
    """No cart side effects."""
    assert assistant.cart(chat["session"])["items"] == []
