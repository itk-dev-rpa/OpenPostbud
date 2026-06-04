"""Tests for shared ORM helpers: status enum, status aggregation, model methods."""

import unittest
from datetime import datetime, timedelta

from OpenPostbud import config
from OpenPostbud.database import db_util
from OpenPostbud.database.common import ShipmentStatus
from OpenPostbud.database.digital_post import letters
from OpenPostbud.database.digital_post.letters import Letter
from OpenPostbud.database.digital_post.shipments import Shipment
from tests import builders
from tests.db_test_case import DBTestCase


class ShipmentStatusEnumTest(unittest.TestCase):
    def test_values(self):
        self.assertEqual(ShipmentStatus.WAITING.value, "Afventer")
        self.assertEqual(ShipmentStatus.SENT.value, "Afsendt")
        self.assertEqual(ShipmentStatus.FAILED.value, "Fejlet")
        self.assertEqual(ShipmentStatus.ABORTED.value, "Afbrudt")


class ModelMethodTest(unittest.TestCase):
    """These methods are pure and need no database."""

    def test_shipment_to_row_dict(self):
        shipment = Shipment(
            id="S-abc",
            name="News",
            created_at=datetime(2024, 3, 9, 14, 30, 0),
            created_by="tester",
        )

        row = shipment.to_row_dict()

        self.assertEqual(row["id"], "S-abc")
        self.assertEqual(row["name"], "News")
        self.assertEqual(row["created_at"], "09/03/2024 14:30:00")
        self.assertEqual(row["created_by"], "tester")

    def test_shipment_deletion_date(self):
        created = datetime(2024, 1, 1, 12, 0, 0)
        shipment = Shipment(created_at=created)

        expected = created + timedelta(days=config.SHIPMENT_LIFETIME_DAYS)
        self.assertEqual(shipment.get_deletion_date(), expected)

    def test_letter_to_row_dict(self):
        letter = Letter(
            id="L-xyz",
            recipient_id="1234567890",
            updated_at=datetime(2024, 3, 9, 14, 30, 0),
            status=ShipmentStatus.SENT,
            message="ok",
        )

        row = letter.to_row_dict()

        self.assertEqual(row["id"], "L-xyz")
        self.assertEqual(row["recipient"], "1234567890")
        self.assertEqual(row["status"], "Afsendt")
        self.assertEqual(row["message"], "ok")


class CalculateShipmentStatusTest(DBTestCase):
    def test_groups_and_counts_by_status_sorted(self):
        shipment_id = builders.make_shipment()
        builders.make_letters(
            shipment_id,
            [
                builders.letter_row(recipient="1111111111"),
                builders.letter_row(recipient="2222222222"),
                builders.letter_row(recipient="3333333333"),
            ],
        )
        # Leave one WAITING, set two to SENT.
        all_letters = letters.get_letters(shipment_id)
        all_letters[0].set_status(ShipmentStatus.SENT)
        all_letters[1].set_status(ShipmentStatus.SENT)

        result = db_util.calculate_shipment_status(shipment_id)

        # Returned as (status value, count) sorted by status text.
        self.assertEqual(result, [("Afsendt", 2), ("Afventer", 1)])


if __name__ == "__main__":
    unittest.main()
