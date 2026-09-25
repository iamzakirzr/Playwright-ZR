"""Repository for ``orders`` and ``order_items``, including the data-integrity queries."""
from db.repositories.base_repository import BaseRepository


class OrderRepository(BaseRepository):
    """Order reads, writes and reconciliation queries."""

    def orders_for_user(self, user_id: int) -> list[dict]:
        """A user's orders, oldest first."""
        return self.fetch_all("SELECT * FROM orders WHERE user_id = ? ORDER BY id", (user_id,))

    def order_total(self, order_id: int) -> float:
        """Sum of quantity times unit price for one order, rounded to cents (0.0 if it has no items)."""
        total = self.scalar(
            "SELECT ROUND(SUM(quantity * unit_price), 2) FROM order_items WHERE order_id = ?",
            (order_id,),
        )
        return total or 0.0

    def revenue_by_status(self) -> dict[str, float]:
        """Revenue grouped by order status, e.g. ``{"PAID": 49.97}``."""
        rows = self.fetch_all(
            """
            SELECT o.status, ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
            FROM orders o JOIN order_items oi ON oi.order_id = o.id
            GROUP BY o.status
            """
        )
        return {r["status"]: r["revenue"] for r in rows}

    def orphan_order_items(self) -> list[dict]:
        """Line items whose parent order no longer exists (should always be empty)."""
        return self.fetch_all(
            """
            SELECT oi.* FROM order_items oi
            LEFT JOIN orders o ON o.id = oi.order_id
            WHERE o.id IS NULL
            """
        )

    def price_mismatches(self) -> list[dict]:
        """Line items whose captured unit price differs from the catalogue price."""
        return self.fetch_all(
            """
            SELECT oi.order_id, p.name, oi.unit_price, p.price
            FROM order_items oi JOIN products p ON p.id = oi.product_id
            WHERE oi.unit_price <> p.price
            """
        )

    def create_order(self, user_id: int, status: str = "PENDING") -> int:
        """Insert an order and return its id. Bad status or user raises ``sqlite3.IntegrityError``."""
        return self.execute("INSERT INTO orders (user_id, status) VALUES (?, ?)", (user_id, status))
