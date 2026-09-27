"""Product catalogue and in-memory carts for the shop assistant."""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field

PRODUCTS: dict[str, float] = {
    "Sauce Labs Backpack": 29.99,
    "Sauce Labs Bike Light": 9.99,
    "Sauce Labs Bolt T-Shirt": 15.99,
    "Sauce Labs Fleece Jacket": 49.99,
    "Sauce Labs Onesie": 7.99,
}


class UnknownProductError(ValueError):
    """Raised when a product name can't be matched to the catalogue."""


#: Shorter names ("s", "a") are substrings of everything, so they never identify a product.
MIN_NAME_CHARS = 3
#: Words shared by every catalogue name; on their own they name no product.
GENERIC_WORDS = {"sauce", "labs", "sauce labs", "product", "item", "items", "products"}


def _short_name(product: str) -> str:
    """Distinctive part of a catalogue name: "Sauce Labs Bike Light" gives "bike light"."""
    return product.lower().removeprefix("sauce labs ").strip()


def resolve_product(name: str) -> str:
    """Map what the model passed as a product ("backpack", "bike lights", or even a
    description such as "soft onesie for little ones") to a catalogue name.

    Raises:
        UnknownProductError: If nothing in the catalogue is a reasonable match.
    """
    wanted = name.strip().lower()
    if len(wanted) < MIN_NAME_CHARS or wanted in GENERIC_WORDS:
        raise UnknownProductError(f"No product matches {name!r}")
    for product in PRODUCTS:
        # Match against the distinctive part only: "labs" or "sauce" must not pick the first product.
        if wanted == product.lower() or wanted.rstrip("s") in _short_name(product):
            return product
    for product in PRODUCTS:
        if _short_name(product) in wanted:
            return product
    close = difflib.get_close_matches(wanted, [p.lower() for p in PRODUCTS], n=1, cutoff=0.5)
    if close:
        return next(p for p in PRODUCTS if p.lower() == close[0])
    raise UnknownProductError(f"No product matches {name!r}")


def mentions_product(text: str, product: str) -> bool:
    """True if ``text`` names ``product`` by any distinctive word: "the jacket", "lights", "t-shirt"."""
    words = re.findall(r"[a-z0-9-]+", (text or "").lower())
    return any(
        word.rstrip("s") == part.rstrip("s")
        for part in _short_name(product).split()
        if len(part) >= 4 and part not in GENERIC_WORDS
        for word in words
    )


def products_named_in(text: str) -> list[str]:
    """Catalogue products that ``text`` names, in catalogue order ("add 2 backpacks" gives the backpack)."""
    return [product for product in PRODUCTS if mentions_product(text, product)]


def cart_lines(view: dict) -> list[str]:
    """``["2 x Sauce Labs Backpack", ...]`` from ``Cart.as_dict()``; the one place cart lines are formatted."""
    return [f"{item['quantity']} x {item['product']}" for item in view["items"]]


@dataclass
class Cart:
    """One session's cart: product name mapped to quantity."""

    items: dict[str, int] = field(default_factory=dict)

    def add(self, product: str, quantity: int = 1) -> None:
        """Add ``quantity`` of a catalogue product.

        Raises:
            ValueError: If ``quantity`` is less than 1.
        """
        if quantity < 1:
            raise ValueError("quantity must be at least 1")
        self.items[product] = self.items.get(product, 0) + quantity

    def remove(self, product: str, quantity: int | None = None) -> bool:
        """Remove ``quantity`` of a product (all of it when None or at least what's there).

        Returns:
            False if the product wasn't in the cart.

        Raises:
            ValueError: If ``quantity`` is less than 1.
        """
        if product not in self.items:
            return False
        if quantity is not None and quantity < 1:
            raise ValueError("quantity must be at least 1")
        if quantity is None or quantity >= self.items[product]:
            del self.items[product]
        else:
            self.items[product] -= quantity
        return True

    def clear(self) -> None:
        """Empty the cart."""
        self.items.clear()

    @property
    def total(self) -> float:
        """Cart total, rounded to cents."""
        return round(sum(PRODUCTS[p] * q for p, q in self.items.items()), 2)

    def as_dict(self) -> dict:
        """JSON-ready view used by the API and by tool results."""
        return {
            "items": [{"product": p, "quantity": q, "unit_price": PRODUCTS[p]} for p, q in sorted(self.items.items())],
            "total": self.total,
        }
