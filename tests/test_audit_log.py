"""Tests for the audit log data layer."""

import unittest

from sqlalchemy import select

from OpenPostbud.database import audit_log, connection
from OpenPostbud.database.audit_log import AuditLog
from tests.db_test_case import DBTestCase


class AuditLogTest(DBTestCase):
    def test_add_log_persists_row(self):
        audit_log.add_log(user="alice", path="/forsendelser")

        with connection.get_session() as session:
            logs = list(session.execute(select(AuditLog)).scalars())

        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].user, "alice")
        self.assertEqual(logs[0].path, "/forsendelser")
        # timestamp gets a default value on insert.
        self.assertIsNotNone(logs[0].timestamp)


if __name__ == "__main__":
    unittest.main()
