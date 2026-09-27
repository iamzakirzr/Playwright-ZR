"""Both shop-agent stacks must expose the same cart tool surface."""

from __future__ import annotations

from ai.chatbot.scripted_chat_model import ScriptedChatModel
from apps.shop_assistant.agent import TOOLS
from apps.shop_assistant.catalog import PRODUCTS, Cart
from apps.shop_assistant.langgraph_agent import LangGraphShopAgent
from apps.shop_assistant.shared import CART_TOOL_NAMES, PRODUCT_ARGUMENT, describe_cart


def test_openai_tools_match_shared_names_and_catalogue_enum():
    """Hand-rolled TOOLS come from shared.py and list every catalogue product."""
    names = [t["function"]["name"] for t in TOOLS]
    assert tuple(names) == CART_TOOL_NAMES
    assert PRODUCT_ARGUMENT["enum"] == list(PRODUCTS)


def test_langgraph_tools_use_the_same_names():
    """LangGraph @tool names must match the shared CART_TOOL_NAMES contract."""
    agent = LangGraphShopAgent(ScriptedChatModel(replies=[]))
    tool_names = {t.name for t in agent.tools}
    assert tool_names >= set(CART_TOOL_NAMES)


def test_describe_cart_empty_and_filled():
    """Shared cart rendering is what both agents put in the system prompt."""
    product = next(iter(PRODUCTS))
    cart = Cart()
    assert describe_cart(cart) == "(empty)"
    cart.add(product, 2)
    text = describe_cart(cart)
    assert product in text and "Total:" in text
