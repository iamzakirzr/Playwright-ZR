from db.repositories.base_repository import BaseRepository


class OrderRepository(BaseRepository):
    def orders_for_user(self, user_id: int) -> list[dict]:
        return self.fetch_all("SELECT * FROM orders WHERE user_id = ? ORDER BY id", (user_id,))

    def order_total(self, order_id: int) -> float:
        total = self.scalar(
            "SELECT ROUND(SUM(quantity * unit_price), 2) FROM order_items WHERE order_id = ?",
            (order_id,),
        )
        return total or 0.0

    def revenue_by_status(self) -> dict[str, float]:
        rows = self.fetch_all(
            """
            SELECT o.status, ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
            FROM orders o JOIN order_items oi ON oi.order_id = o.id
            GROUP BY o.status
            """
        )
        return {r["status"]: r["revenue"] for r in rows}

    def orphan_order_items(self) -> list[dict]:
        return self.fetch_all(
            """
            SELECT oi.* FROM order_items oi
            LEFT JOIN orders o ON o.id = oi.order_id
            WHERE o.id IS NULL
            """
        )

    def price_mismatches(self) -> list[dict]:
        """Line items whose captured unit_price drifts from the catalogue price."""
        return self.fetch_all(
            """
            SELECT oi.order_id, p.name, oi.unit_price, p.price
            FROM order_items oi JOIN products p ON p.id = oi.product_id
            WHERE oi.unit_price <> p.price
            """
        )

    def create_order(self, user_id: int, status: str = "PENDING") -> int:
        return self.execute("INSERT INTO orders (user_id, status) VALUES (?, ?)", (user_id, status))
