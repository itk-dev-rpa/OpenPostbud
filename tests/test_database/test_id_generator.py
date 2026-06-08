"""Tests for the id generator helper (pure functions, no database needed)."""

import unittest

from OpenPostbud.database.data_types.id_generator import create_id


class CreateIdTest(unittest.TestCase):
    def test_starts_with_prefix(self):
        gen = create_id("S-", 10)
        self.assertTrue(gen().startswith("S-"))

    def test_total_length_is_prefix_plus_length(self):
        gen = create_id("L-", 10)
        self.assertEqual(len(gen()), len("L-") + 10)

    def test_empty_prefix(self):
        gen = create_id("", 5)
        self.assertEqual(len(gen()), 5)

    def test_random_part_uses_documented_charset(self):
        gen = create_id("X-", 20)
        random_part = gen()[len("X-"):]
        allowed = set("abcdefghijklmnopqrstuvwxyz0123456789")
        self.assertTrue(set(random_part).issubset(allowed))

    def test_ids_are_distinct(self):
        gen = create_id("S-", 10)
        ids = {gen() for _ in range(1000)}
        # Collisions are astronomically unlikely with 36^10 of space.
        self.assertEqual(len(ids), 1000)


if __name__ == "__main__":
    unittest.main()
