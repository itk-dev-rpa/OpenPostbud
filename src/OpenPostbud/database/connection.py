"""This module contains common static functions to interact with the database."""

from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from OpenPostbud.database import base


def get_session() -> Session:
    """Get the shared global connection
    The row factory is set to sqlite3.Row.

    Returns:
        The shared database connection.
    """
    _get_connection_engine()

    return Session(_get_connection_engine(), expire_on_commit=False)


def create_tables():
    """Create all database tables that don't already exists."""
    _get_connection_engine()
    base.create_tables(_get_connection_engine())


@lru_cache(maxsize=1)
def _get_connection_engine() -> Engine:
    """Connect to the database."""
    return create_engine("sqlite+pysqlite:///database.db")
