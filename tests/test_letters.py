"""Tests for the letter data layer: creation from csv rows, status changes, abort."""

import json
import unittest

from OpenPostbud.database.common import ShipmentStatus
from OpenPostbud.database.digital_post import letters
from OpenPostbud.database.digital_post.letters import MemoFields
from tests import builders
from tests.db_test_case import DBTestCase


class AddLettersTest(DBTestCase):
    def test_recipient_extracted_and_rest_stored_as_field_data(self):
        shipment_id = builders.make_shipment()
        builders.make_letters(
            shipment_id,
            [builders.letter_row(recipient="2512481234", Navn="Hans", By="Aarhus")],
        )

        result = letters.get_letters(shipment_id)

        self.assertEqual(len(result), 1)
        letter = result[0]
        self.assertEqual(letter.recipient_id, "2512481234")
        # The recipient column must not leak into field_data.
        field_data = json.loads(letter.field_data)
        self.assertNotIn(MemoFields.MEMO_MODTAGER.key, field_data)
        self.assertEqual(field_data, {"Navn": "Hans", "By": "Aarhus"})

    def test_generated_id_and_default_status(self):
        shipment_id = builders.make_shipment()
        builders.make_letters(shipment_id, [builders.letter_row()])

        letter = letters.get_letters(shipment_id)[0]

        self.assertTrue(letter.id.startswith("L-"))
        self.assertEqual(letter.status, ShipmentStatus.WAITING)

    def test_get_letters_scoped_to_shipment(self):
        shipment_a = builders.make_shipment(name="A")
        shipment_b = builders.make_shipment(name="B")
        builders.make_letters(shipment_a, [builders.letter_row(recipient="1111111111")])
        builders.make_letters(shipment_b, [builders.letter_row(recipient="2222222222")])

        result = letters.get_letters(shipment_a)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].recipient_id, "1111111111")


class LetterStatusTest(DBTestCase):
    def test_set_status_updates_status_and_message(self):
        shipment_id = builders.make_shipment()
        builders.make_letters(shipment_id, [builders.letter_row()])
        letter = letters.get_letters(shipment_id)[0]

        letter.set_status(ShipmentStatus.FAILED, message="Something went wrong")

        updated = letters.get_letters(shipment_id)[0]
        self.assertEqual(updated.status, ShipmentStatus.FAILED)
        self.assertEqual(updated.message, "Something went wrong")

    def test_set_status_keeps_transaction_id_when_none(self):
        shipment_id = builders.make_shipment()
        builders.make_letters(shipment_id, [builders.letter_row()])
        letter = letters.get_letters(shipment_id)[0]

        letter.set_status(ShipmentStatus.SENT, transaction_id="tx-123")
        letter.set_status(ShipmentStatus.DELIVERED)  # no transaction_id given

        updated = letters.get_letters(shipment_id)[0]
        self.assertEqual(updated.status, ShipmentStatus.DELIVERED)
        self.assertEqual(updated.transaction_id, "tx-123")

    def test_abort_letters_only_affects_waiting(self):
        shipment_id = builders.make_shipment()
        builders.make_letters(
            shipment_id,
            [
                builders.letter_row(recipient="1111111111"),
                builders.letter_row(recipient="2222222222"),
            ],
        )
        all_letters = letters.get_letters(shipment_id)
        # Move one letter out of WAITING so abort should skip it.
        all_letters[0].set_status(ShipmentStatus.SENT)

        letters.abort_letters(shipment_id, user="tester")

        by_id = {letter.id: letter for letter in letters.get_letters(shipment_id)}
        self.assertEqual(by_id[all_letters[0].id].status, ShipmentStatus.SENT)
        aborted = by_id[all_letters[1].id]
        self.assertEqual(aborted.status, ShipmentStatus.ABORTED)
        self.assertEqual(aborted.message, "Afbrudt af tester")


if __name__ == "__main__":
    unittest.main()
