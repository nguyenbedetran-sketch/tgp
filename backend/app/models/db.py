"""
Lightweight SQLite data-access layer.

The project intentionally avoids an ORM dependency (SQLAlchemy is not
resolvable in this offline build environment - see README "Vi sao khong
dung SQLAlchemy") and instead uses Python's built-in `sqlite3` module with
a thin helper layer:

  - one connection per request, stored on Flask's `g` and closed automatically
  - row_factory returns dict-like rows (sqlite3.Row) so callers can do row["col"]
  - init_db() applies database/schema.sql idempotently (CREATE TABLE IF NOT EXISTS)

This is a real, working persistence layer - not a mock - every API route
reads/writes through here.
"""
import sqlite3
from pathlib import Path

from flask import g

from app.config.settings import config


def _connect() -> sqlite3.Connection:
    db_path = Path(config.DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db() -> sqlite3.Connection:
    """Return the request-scoped SQLite connection, creating it if needed."""
    if "db" not in g:
        g.db = _connect()
    return g.db


def close_db(_exception=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db():
    """Apply schema.sql against the configured database file. Safe to call
    on every startup: all statements are CREATE TABLE/INDEX IF NOT EXISTS."""
    schema_path = Path(__file__).resolve().parent.parent.parent.parent / "database" / "schema.sql"
    conn = _connect()
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()
    finally:
        conn.close()


def register_teardown(app):
    app.teardown_appcontext(close_db)
