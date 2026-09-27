"""Helpers shared by the hand-rolled agent and the LangGraph agent.

Keeping cart rendering (and other cross-implementation details) here prevents the two teaching
implementations from drifting on the surface the model actually sees.
"""

from __future__ import annotations

from apps.shop_assistant.catalog import Cart, cart_lines


def describe_cart(cart: Cart) -> str:
    """One line per item plus the total, as the model sees it in CURRENT CART.

    Giving the model the live cart every turn means it never has to remember or guess it:
    before this, asked "what's in my cart now?", it invented three items and a total.
    """
    view = cart.as_dict()
    if not view["items"]:
        return "(empty)"
    return "\n".join([*(f"- {line}" for line in cart_lines(view)), f"Total: ${view['total']:.2f}"])
