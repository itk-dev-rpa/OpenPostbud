"""This module contains common static functions to interact with the database."""

from functools import lru_cache

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session

from OpenPostbud.database import base


DATABASE_PATH = "database.db"


def get_session() -> Session:
    """Get a new database session."""
    return Session(get_connection_engine(), expire_on_commit=False)


def create_tables():
    """Create all database tables that don't already exists."""
    base.create_tables(get_connection_engine())


@lru_cache(maxsize=1)
def get_connection_engine() -> Engine:
    """Connect to the database."""
    return create_engine(f"sqlite+pysqlite:///{DATABASE_PATH}")


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, _):
    """An eventlistener that will set PRAGMA
    options on every new connection to the database.
    """
    dbapi_connection.execute("PRAGMA foreign_keys=ON")
    dbapi_connection.commit()
