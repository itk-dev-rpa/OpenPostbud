
from sqlalchemy import Engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SqlAlchemy base class for all ORM classes in this module."""


def create_tables(engine: Engine):
    """Create all SQL tables related to ORM classes in this module.

    Args:
        engine: The SqlAlchemy connection engine used to create the tables.
    """
    Base.metadata.create_all(engine)
