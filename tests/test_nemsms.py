"""Tests for the NemSMS data layer: shipments, messages, status changes, cleanup."""

import unittest
from datetime import datetime, timedelta

from OpenPostbud.database import connection
from OpenPostbud.database.common import ShipmentStatus
from OpenPostbud.database.nemsms import nemsms_messages, nemsms_shipments
from OpenPostbud.database.nemsms.nemsms_shipments import NemSMSShipment
from tests.db_test_case import DBTestCase


def _make_shipment(name="SMS Campaign", owner_group="GroupA") -> str:
    return nemsms_shipments.add_shipment(
        name=name,
        description="desc",
        message_text="Hello",
        created_by="tester",
        owner_group=owner_group,
    )


def _set_deletion_date(shipment_id: str, deletion_date: datetime):
    with connection.get_session() as session:
        shipment = session.get(NemSMSShipment, shipment_id)
        shipment.deletion_date = deletion_date
        session.commit()


class NemSMSShipmentTest(DBTestCase):
    def test_add_and_get_shipment(self):
        shipment_id = _make_shipment(name="Campaign", owner_group="GroupA")

        shipment = nemsms_shipments.get_shipment(shipment_id)

        self.assertTrue(shipment_id.startswith("NS-"))
        self.assertEqual(shipment.name, "Campaign")
        self.assertEqual(shipment.message_text, "Hello")
        self.assertEqual(shipment.owner_group, "GroupA")

    def test_get_shipments_filters_by_group(self):
        _make_shipment(name="A", owner_group="GroupA")
        _make_shipment(name="B", owner_group="GroupB")

        result = nemsms_shipments.get_shipments(groups=["GroupA"])

        self.assertEqual({s.name for s in result}, {"A"})

    def test_get_shipment_ownership_check(self):
        shipment_id = _make_shipment(owner_group="GroupA")

        self.assertIsNone(nemsms_shipments.get_shipment(shipment_id, groups=["GroupB"]))
        self.assertIsNotNone(nemsms_shipments.get_shipment(shipment_id, groups=["GroupA"]))

    def test_delete_old_shipments_cascades_to_messages(self):
        old_id = _make_shipment(name="old")
        recent_id = _make_shipment(name="recent")
        nemsms_messages.add_messages(old_id, ["1111111111"])
        _set_deletion_date(old_id, datetime.today() - timedelta(days=1))

        nemsms_shipments.delete_old_shipments()

        remaining = nemsms_shipments.get_shipments()
        self.assertEqual({s.id for s in remaining}, {recent_id})
        self.assertEqual(len(nemsms_messages.get_messages(old_id)), 0)


class NemSMSMessageTest(DBTestCase):
    def test_add_messages_defaults(self):
        shipment_id = _make_shipment()
        nemsms_messages.add_messages(shipment_id, ["1111111111", "2222222222"])

        messages = nemsms_messages.get_messages(shipment_id)

        self.assertEqual(len(messages), 2)
        self.assertTrue(all(m.id.startswith("NM-") for m in messages))
        self.assertTrue(all(m.status == ShipmentStatus.WAITING for m in messages))
        self.assertEqual({m.recipient_id for m in messages}, {"1111111111", "2222222222"})

    def test_get_messages_scoped_to_shipment(self):
        shipment_a = _make_shipment(name="A")
        shipment_b = _make_shipment(name="B")
        nemsms_messages.add_messages(shipment_a, ["1111111111"])
        nemsms_messages.add_messages(shipment_b, ["2222222222"])

        result = nemsms_messages.get_messages(shipment_a)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].recipient_id, "1111111111")

    def test_set_status_keeps_transaction_id_when_none(self):
        shipment_id = _make_shipment()
        nemsms_messages.add_messages(shipment_id, ["1111111111"])
        message = nemsms_messages.get_messages(shipment_id)[0]

        message.set_status(ShipmentStatus.SENT, transaction_id="tx-1")
        message.set_status(ShipmentStatus.DELIVERED, message="done")

        updated = nemsms_messages.get_messages(shipment_id)[0]
        self.assertEqual(updated.status, ShipmentStatus.DELIVERED)
        self.assertEqual(updated.status_message, "done")
        self.assertEqual(updated.transaction_id, "tx-1")

    def test_abort_messages_only_affects_waiting(self):
        shipment_id = _make_shipment()
        nemsms_messages.add_messages(shipment_id, ["1111111111", "2222222222"])
        messages = nemsms_messages.get_messages(shipment_id)
        messages[0].set_status(ShipmentStatus.SENT)

        nemsms_messages.abort_messages(shipment_id, user="tester")

        by_id = {m.id: m for m in nemsms_messages.get_messages(shipment_id)}
        self.assertEqual(by_id[messages[0].id].status, ShipmentStatus.SENT)
        aborted = by_id[messages[1].id]
        self.assertEqual(aborted.status, ShipmentStatus.ABORTED)
        self.assertEqual(aborted.status_message, "Afbrudt af tester")


if __name__ == "__main__":
    unittest.main()
