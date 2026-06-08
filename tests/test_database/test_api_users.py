"""Tests for the api user data layer, including group filtering and key verification."""

import unittest

from OpenPostbud.database import api_users
from tests.test_database.db_test_case import DBTestCase


class ApiUserTest(DBTestCase):
    def test_create_returns_id_dot_key_and_hashes_key(self):
        api_key = api_users.create_api_user("My App", "GroupA")

        self.assertRegex(api_key, r"^[\w-]+\.[\w-]+$")

        id_part, key_part = api_key.split(".")
        users = api_users.get_api_users()
        self.assertEqual(len(users), 1)
        stored = users[0]
        self.assertEqual(stored.id, id_part)
        # The raw key must not be stored; only a hash.
        self.assertNotEqual(stored.key_hash, key_part)
        self.assertNotIn(key_part, stored.key_hash)

    def test_verify_valid_key_returns_user(self):
        api_key = api_users.create_api_user("My App", "GroupA")

        user = api_users.verify_api_key(api_key)

        self.assertIsNotNone(user)
        self.assertEqual(user.name, "My App")

    def test_verify_malformed_key_returns_none(self):
        self.assertIsNone(api_users.verify_api_key("not-a-valid-key"))

    def test_verify_wrong_key_returns_none(self):
        api_key = api_users.create_api_user("My App", "GroupA")
        id_part, _ = api_key.split(".")

        self.assertIsNone(api_users.verify_api_key(f"{id_part}.wrongkey"))

    def test_verify_unknown_id_returns_none(self):
        self.assertIsNone(api_users.verify_api_key("unknown.somekey"))

    def test_get_api_users_filters_by_group(self):
        api_users.create_api_user("App A", "GroupA")
        api_users.create_api_user("App B", "GroupB")

        group_a = api_users.get_api_users(groups=["GroupA"])
        self.assertEqual({u.name for u in group_a}, {"App A"})

    def test_get_api_users_none_returns_all(self):
        api_users.create_api_user("App A", "GroupA")
        api_users.create_api_user("App B", "GroupB")

        self.assertEqual(len(api_users.get_api_users(groups=None)), 2)

    def test_delete_api_user(self):
        api_key = api_users.create_api_user("My App", "GroupA")
        id_part, _ = api_key.split(".")

        self.assertTrue(api_users.delete_api_user(id_part))
        self.assertFalse(api_users.delete_api_user(id_part))
        self.assertEqual(len(api_users.get_api_users()), 0)


if __name__ == "__main__":
    unittest.main()
