"""Product catalogue and in-memory carts for the shop assistant."""

from __future__ import annotations

import difflib
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
    for product in PRODUCTS:
        if wanted == product.lower() or wanted.rstrip("s") in product.lower():
            return product
    for product in PRODUCTS:
        if _short_name(product) in wanted:
            return product
    close = difflib.get_close_matches(wanted, [p.lower() for p in PRODUCTS], n=1, cutoff=0.5)
    if close:
        return next(p for p in PRODUCTS if p.lower() == close[0])
    raise UnknownProductError(f"No product matches {name!r}")


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

    def remove(self, product: str) -> bool:
        """Remove a product entirely; return False if it wasn't in the cart."""
        return self.items.pop(product, None) is not None

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
