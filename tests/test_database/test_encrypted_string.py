"""Tests that the EncryptedString column type round-trips through the database."""

import unittest

from sqlalchemy import text

from OpenPostbud.database.digital_post import letters
from tests.test_database import builders
from tests.test_database.db_test_case import DBTestCase


class EncryptedStringTest(DBTestCase):
    def test_recipient_round_trips(self):
        shipment_id = builders.make_shipment()
        builders.make_letters(
            shipment_id, [builders.letter_row(recipient="2512481234")]
        )

        result = letters.get_letters(shipment_id)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].recipient_id, "2512481234")

    def test_field_data_round_trips(self):
        shipment_id = builders.make_shipment()
        builders.make_letters(
            shipment_id,
            [builders.letter_row(recipient="2512481234", Navn="Hans Hansen")],
        )

        result = letters.get_letters(shipment_id)

        # field_data is the json-encoded remainder of the row.
        self.assertIn("Hans Hansen", result[0].field_data)

    def test_stored_value_is_encrypted_not_plaintext(self):
        shipment_id = builders.make_shipment()
        builders.make_letters(
            shipment_id, [builders.letter_row(recipient="2512481234")]
        )

        # Read the raw column bypassing the type decorator.
        with self.engine.connect() as conn:
            raw = conn.execute(text("SELECT recipient_id FROM Letters")).scalar()

        self.assertNotIn(b"2512481234", raw)


if __name__ == "__main__":
    unittest.main()
