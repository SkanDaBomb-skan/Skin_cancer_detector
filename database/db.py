"""
Database Module
===============
SQLite database initialization and helper utilities.
Uses SQLite for zero-configuration setup — no external DB server needed.
"""

import os
import sqlite3
from contextlib import contextmanager
from config import Config


def get_db_path() -> str:
    """Return the absolute path to the SQLite database file."""
    return Config.DATABASE_PATH


def init_db() -> None:
    """
    Create database tables if they don't already exist.

    Tables:
        predictions — stores every analysis performed by the system
    """
    os.makedirs(os.path.dirname(get_db_path()), exist_ok=True)

    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path    TEXT    NOT NULL,
                original_name TEXT    NOT NULL,
                diagnosis     TEXT    NOT NULL,
                short_code    TEXT    NOT NULL,
                risk_level    TEXT    NOT NULL,
                confidence    REAL    NOT NULL,
                description   TEXT,
                recommendation TEXT,
                top_3_json    TEXT,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


@contextmanager
def get_connection():
    """
    Context manager that yields a SQLite connection and ensures it is
    properly closed, even when an exception occurs.
    """
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row  # access columns by name
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
