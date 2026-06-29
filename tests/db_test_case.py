"""Reusable unittest base class providing an isolated in-memory database."""

import unittest
from unittest import mock

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from OpenPostbud.database import connection


class DatabaseTestCase(unittest.TestCase):
    """Base test case that swaps the application database for an isolated
    in-memory SQLite database.

    The connection engine is patched with an in-memory engine, so tests never
    touch the application database. StaticPool keeps a single underlying
    connection alive so the schema and data persist across the separate
    sessions opened by the code under test.

    All ORM tables registered on the metadata (i.e. whose modules have been
    imported) are created, so subclasses only need to import the models they
    exercise.
    """

    def setUp(self):
        super().setUp()
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        # Patch before creating tables so create_tables uses the in-memory engine.
        patcher = mock.patch.object(connection, "get_connection_engine", return_value=self.engine)
        self.addCleanup(patcher.stop)
        patcher.start()
        self.addCleanup(self.engine.dispose)

        connection.create_tables()
