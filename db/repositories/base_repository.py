"""Repository base: the SQL-layer equivalent of a page object.

Tests call intent methods (``find_by_username``) instead of embedding SQL.
Every query is parameterised with ``?`` placeholders, never string-formatted,
so test data can't cause SQL injection either.
"""

from __future__ import annotations

import sqlite3
from typing import Any


class BaseRepository:
    """Query helpers shared by every repository.

    Args:
        conn: An open DB-API connection (the per-test transaction from the ``db`` fixture).
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        """Keep the connection; repositories never open or commit transactions themselves."""
        self.conn = conn

    def fetch_one(self, sql: str, params: tuple[Any, ...] = ()) -> dict | None:
        """First row as a dict, or None when there are no rows."""
        row = self.conn.execute(sql, params).fetchone()
        return dict(row) if row else None

    def fetch_all(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict]:
        """All rows as a list of dicts."""
        return [dict(r) for r in self.conn.execute(sql, params).fetchall()]

    def scalar(self, sql: str, params: tuple[Any, ...] = ()) -> Any:
        """First column of the first row (for COUNT, SUM and similar), or None."""
        row = self.conn.execute(sql, params).fetchone()
        return row[0] if row else None

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> int:
        """Run a write statement and return ``lastrowid`` (the new id for INSERTs)."""
        return self.conn.execute(sql, params).lastrowid
