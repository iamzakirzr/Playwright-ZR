"""Helpers shared by the hand-rolled agent and the LangGraph agent.

Keeping cart rendering and the OpenAI-style tool schema here prevents the two teaching
implementations from drifting on the surface the model actually sees. LangGraph still
declares tools with ``@tool`` (type hints → JSON schema), but both stacks must expose the
same tool *names* and catalogue enum — pinned by unit tests.
"""

from __future__ import annotations

from apps.shop_assistant.catalog import PRODUCTS, Cart, cart_lines

#: Cart tool names both agent implementations must expose (trajectory assertions compare these).
CART_TOOL_NAMES = ("add_to_cart", "remove_from_cart", "view_cart")

#: The product argument lists the catalogue as an ``enum``. With only a free-text description
#: ("Product name"), qwen2.5:1.5b on some CPUs copied the description itself as the value.
PRODUCT_ARGUMENT = {
    "type": "string",
    "enum": list(PRODUCTS),
    "description": "The catalogue product the user named",
}

#: OpenAI-compatible tool definitions for the hand-rolled Ollama loop in ``agent.py``.
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_to_cart",
            "description": "Add a product to the shopping cart",
            "parameters": {
                "type": "object",
                "properties": {
                    "product": PRODUCT_ARGUMENT,
                    "quantity": {"type": "integer", "minimum": 1},
                },
                "required": ["product", "quantity"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remove_from_cart",
            "description": "Remove some or all of a product from the shopping cart",
            "parameters": {
                "type": "object",
                "properties": {
                    "product": PRODUCT_ARGUMENT,
                    "quantity": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "How many to remove; to remove all, use the quantity shown in CURRENT CART",
                    },
                },
                "required": ["product", "quantity"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "view_cart",
            "description": "Show what is in the shopping cart and its total",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


def describe_cart(cart: Cart) -> str:
    """One line per item plus the total, as the model sees it in CURRENT CART.

    Giving the model the live cart every turn means it never has to remember or guess it:
    before this, asked "what's in my cart now?", it invented three items and a total.
    """
    view = cart.as_dict()
    if not view["items"]:
        return "(empty)"
    return "\n".join([*(f"- {line}" for line in cart_lines(view)), f"Total: ${view['total']:.2f}"])
