from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from OpenPostbud.database import base

_connection_engine: Engine | None = None


def get_session() -> Session:
    """Get the shared global connection
    The row factory is set to sqlite3.Row.

    Returns:
        The shared database connection.
    """
    _connect()

    return Session(_connection_engine, expire_on_commit=False)


def _connect():
    """Connect to the database."""
    global _connection_engine

    if not _connection_engine:
        _connection_engine = create_engine("sqlite+pysqlite:///database.db")


def create_tables():
    """Create all database tables that don't already exists."""
    _connect()
    global _connection_engine
    base.create_tables(_connection_engine)