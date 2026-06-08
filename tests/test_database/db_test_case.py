"""A base test case that gives each test an isolated, throwaway database.

The database layer always goes through ``connection.get_connection_engine()``
(see `OpenPostbud.database.connection`). By patching that function to return
an engine bound to a temporary SQLite file, every ``connection.get_session()``
call made by the production code is transparently redirected to the test
database. The schema is built by running the real migration SQL files, so the
tests exercise the exact production schema.
"""

import contextlib
import io
import logging
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine

from OpenPostbud.database import connection
from OpenPostbud.database.migrations import migrate


class DBTestCase(unittest.TestCase):
    """Base class for tests that need a live (but disposable) database."""

    def setUp(self):
        # Production code logs at INFO (config.py configures the root logger on
        # import); silence it so it doesn't clutter the test output.
        logging.disable(logging.CRITICAL)
        self.addCleanup(logging.disable, logging.NOTSET)

        self._tmpdir = tempfile.mkdtemp(prefix="openpostbud_test_")
        db_path = os.path.join(self._tmpdir, "test.db")
        self.engine = create_engine(f"sqlite+pysqlite:///{db_path}")

        # Redirect all get_session()/get_connection_engine() calls to our engine.
        self._patcher = patch.object(
            connection, "get_connection_engine", return_value=self.engine
        )
        self._patcher.start()

        # Build the schema from the real migration files (uses the patched engine).
        # perform_step prints progress; swallow it to keep test output clean.
        with contextlib.redirect_stdout(io.StringIO()):
            migrate.create_migrations_table()
            for sql_file in sorted(migrate.MIGRATIONS_FOLDER.iterdir()):
                migrate.perform_step(sql_file)

    def tearDown(self):
        self._patcher.stop()
        self.engine.dispose()
        # Guard against any cached real engine leaking into later tests.
        connection.get_connection_engine.cache_clear()
        shutil.rmtree(self._tmpdir, ignore_errors=True)
