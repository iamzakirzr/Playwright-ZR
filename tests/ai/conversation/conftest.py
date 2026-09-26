"""Reference conversations for calibrating the conversational metrics."""

import pytest
from deepeval.test_case import ConversationalTestCase, Turn

ROLE = "A polite shopping assistant for the Sauce Demo Store that only helps with products, carts and store policies."


def _turns(*pairs: tuple[str, str]) -> list[Turn]:
    """Alternate user/assistant turns from (user, assistant) pairs."""
    turns = []
    for user, assistant in pairs:
        turns += [Turn(role="user", content=user), Turn(role="assistant", content=assistant)]
    return turns


@pytest.fixture(scope="session")
def good_conversation() -> ConversationalTestCase:
    """Remembers the order number, answers the policy question, stays in role."""
    return ConversationalTestCase(
        chatbot_role=ROLE,
        turns=_turns(
            ("Hi, I'm Priya. My order number is 4471.", "Hi Priya! How can I help with order 4471?"),
            (
                "Can I still return the jacket from it?",
                "Yes. Returns are accepted within 45 days of delivery if the item is unused and in its original packaging.",
            ),
            ("Great, and what was my order number again?", "Your order number is 4471."),
        ),
    )


@pytest.fixture(scope="session")
def bad_conversation() -> ConversationalTestCase:
    """Ignores the question, leaves its role, and re-asks what the user already said."""
    return ConversationalTestCase(
        chatbot_role=ROLE,
        turns=_turns(
            ("Hi, I'm Priya. My order number is 4471.", "Hi! How can I help?"),
            ("Can I still return the jacket from it?", "Here is a poem about the sea: the waves roll in and out."),
            ("Great, and what was my order number again?", "Could you tell me your order number and your name?"),
        ),
    )
