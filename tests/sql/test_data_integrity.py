"""Data-integrity checks: aggregates, referential integrity, constraints and cascades."""

import sqlite3

import pytest


def test_order_total_is_sum_of_line_items(order_repo):
    """An order total equals the sum of quantity times unit price."""
    assert order_repo.order_total(1) == pytest.approx(29.99 + 2 * 9.99)


def test_revenue_aggregation_by_status(order_repo):
    """GROUP BY revenue per status matches the hand-computed values."""
    assert order_repo.revenue_by_status() == {
        "PAID": pytest.approx(49.97),
        "PENDING": pytest.approx(49.99),
        "SHIPPED": pytest.approx(23.97),
    }


def test_no_orphan_order_items(order_repo):
    """No line item points at a missing order."""
    assert order_repo.orphan_order_items() == []


def test_line_item_prices_match_catalogue(order_repo):
    """Captured unit prices match the product catalogue."""
    assert order_repo.price_mismatches() == []


def test_deleting_user_cascades_to_orders(user_repo, order_repo):
    """Deleting a user removes their orders and leaves no orphaned items."""
    user_id = user_repo.find_by_username("standard_user")["id"]
    assert order_repo.orders_for_user(user_id)

    user_repo.delete(user_id)

    assert order_repo.orders_for_user(user_id) == []
    assert order_repo.orphan_order_items() == []


def test_order_status_is_constrained(order_repo):
    """The CHECK constraint rejects an unknown order status."""
    with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
        order_repo.create_order(user_id=1, status="LOST")


def test_order_requires_existing_user(order_repo):
    """The foreign key rejects an order for a non-existent user."""
    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
        order_repo.create_order(user_id=9999)
