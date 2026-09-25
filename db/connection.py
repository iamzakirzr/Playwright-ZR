"""SQLite connection factory.

SQLite keeps the suite zero-infrastructure. Swapping to Postgres means
replacing this module (e.g. psycopg) — repositories only depend on a DB-API
connection and use `?` placeholders.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

SEED_FILE = Path(__file__).with_name("seed.sql")


def create_connection(db_path: str = ":memory:", seed: bool = True) -> sqlite3.Connection:
    # isolation_level=None -> autocommit off is managed explicitly by the fixture (BEGIN/ROLLBACK).
    conn = sqlite3.connect(db_path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    if seed:
        conn.executescript(SEED_FILE.read_text())
    return conn
