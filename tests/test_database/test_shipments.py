"""Tests for the shipment data layer: CRUD, group filtering and cleanup/cascade."""

import unittest
from datetime import datetime, timedelta

from OpenPostbud import config
from OpenPostbud.database import connection
from OpenPostbud.database.digital_post import letters, shipments
from OpenPostbud.database.digital_post.shipments import Shipment
from tests.test_database import builders
from tests.test_database.db_test_case import DBTestCase


def _set_created_at(shipment_id: str, created_at: datetime):
    """Backdate a shipment's created_at (add_shipment always uses 'now')."""
    with connection.get_session() as session:
        shipment = session.get(Shipment, shipment_id)
        shipment.created_at = created_at
        session.commit()


class ShipmentCrudTest(DBTestCase):
    def test_add_and_get_shipment(self):
        shipment_id = builders.make_shipment(name="Newsletter", owner_group="GroupA")

        shipment = shipments.get_shipment(shipment_id)

        self.assertIsNotNone(shipment)
        self.assertEqual(shipment.name, "Newsletter")
        self.assertEqual(shipment.owner_group, "GroupA")

    def test_get_shipments_filters_by_group(self):
        builders.make_shipment(name="A", owner_group="GroupA")
        builders.make_shipment(name="B", owner_group="GroupB")

        result = shipments.get_shipments(groups=["GroupA"])

        self.assertEqual({s.name for s in result}, {"A"})

    def test_get_shipments_none_returns_all(self):
        builders.make_shipment(owner_group="GroupA")
        builders.make_shipment(owner_group="GroupB")

        self.assertEqual(len(shipments.get_shipments(groups=None)), 2)

    def test_get_shipments_ordered_by_created_at_desc(self):
        old_id = builders.make_shipment(name="old")
        new_id = builders.make_shipment(name="new")
        _set_created_at(old_id, datetime(2020, 1, 1))
        _set_created_at(new_id, datetime(2024, 1, 1))

        result = shipments.get_shipments()

        self.assertEqual([s.id for s in result], [new_id, old_id])

    def test_get_shipment_ownership_check_blocks_other_group(self):
        shipment_id = builders.make_shipment(owner_group="GroupA")

        self.assertIsNone(shipments.get_shipment(shipment_id, groups=["GroupB"]))
        self.assertIsNotNone(shipments.get_shipment(shipment_id, groups=["GroupA"]))


class DeleteOldShipmentsTest(DBTestCase):
    def test_deletes_only_old_shipments_and_cascades_to_letters(self):
        old_id = builders.make_shipment(name="old")
        recent_id = builders.make_shipment(name="recent")
        builders.make_letters(old_id, [builders.letter_row(recipient="1111111111")])

        _set_created_at(
            old_id,
            datetime.now() - timedelta(days=config.SHIPMENT_LIFETIME_DAYS + 1),
        )

        shipments.delete_old_shipments()

        remaining = shipments.get_shipments()
        self.assertEqual({s.id for s in remaining}, {recent_id})
        # The old shipment's letters were removed by the FK cascade.
        self.assertEqual(len(letters.get_letters(old_id)), 0)


if __name__ == "__main__":
    unittest.main()
