"""SQLite connection factory.

SQLite keeps the suite zero-infrastructure. Moving to Postgres means
replacing this module (for example with psycopg); repositories depend only
on a DB-API connection.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

SEED_FILE = Path(__file__).with_name("seed.sql")


def create_connection(db_path: str = ":memory:", seed: bool = True) -> sqlite3.Connection:
    """Open a connection with dict-like rows and foreign keys enforced.

    Args:
        db_path: File path, or ``:memory:`` for a throw-away database.
        seed: Run ``seed.sql`` (schema and fixtures) after connecting.

    Returns:
        A connection in autocommit mode (``isolation_level=None``). The test
        fixture manages transactions explicitly with BEGIN and ROLLBACK.
    """
    conn = sqlite3.connect(db_path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    if seed:
        conn.executescript(SEED_FILE.read_text())
    return conn
