"""Repository base: the SQL-layer equivalent of a page object.

Tests call intent methods (`find_by_username`) rather than embedding SQL.
All queries are parameterised.
"""
from __future__ import annotations

import sqlite3
from typing import Any


class BaseRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def fetch_one(self, sql: str, params: tuple[Any, ...] = ()) -> dict | None:
        row = self.conn.execute(sql, params).fetchone()
        return dict(row) if row else None

    def fetch_all(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict]:
        return [dict(r) for r in self.conn.execute(sql, params).fetchall()]

    def scalar(self, sql: str, params: tuple[Any, ...] = ()) -> Any:
        row = self.conn.execute(sql, params).fetchone()
        return row[0] if row else None

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> int:
        """Returns lastrowid for inserts."""
        return self.conn.execute(sql, params).lastrowid
