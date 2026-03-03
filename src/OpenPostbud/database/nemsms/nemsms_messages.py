"""This module contains the NemSMS message ORM class."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, insert, select, String, update
from sqlalchemy.orm import Mapped, mapped_column

from OpenPostbud.database.base import Base
from OpenPostbud.database import connection
from OpenPostbud.database.data_types.encrypted_string import EncryptedString
from OpenPostbud.database.data_types.id_generator import create_id
from OpenPostbud.database.common import ShipmentStatus


class NemSMSMessage(Base):
    """An ORM class representing a NemSMS message."""
    __tablename__ = "NemSMS_Messages"

    id: Mapped[str] = mapped_column(String(13), primary_key=True, default=create_id("NM-", 10))
    shipment_id: Mapped[str] = mapped_column(ForeignKey("NemSMS_Shipments.id", ondelete="CASCADE"))
    recipient_id: Mapped[str] = mapped_column(EncryptedString())
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now)
    status: Mapped[ShipmentStatus] = mapped_column(default=ShipmentStatus.WAITING)
    status_message: Mapped[str] = mapped_column(String(100), nullable=True)
    transaction_id: Mapped[str] = mapped_column(nullable=True)

    def to_row_dict(self) -> dict[str, str]:
        """Convert to a dictionary to be shown in a table."""
        return {
            "id": str(self.id),
            "recipient": f"{self.recipient_id[:6]}-{self.recipient_id[6:]}",
            "updated_at": self.updated_at.strftime("%d/%m/%Y %H:%M:%S"),
            "status": self.status.value,
            "message": self.status_message
        }

    def set_status(self, status: ShipmentStatus, transaction_id: str | None = None, message: str | None = None):
        """Set the status of the message in the database.
        The transaction id is not overwritten if the given value is None.

        Args:
            status: The status to set on the message.
            transaction_id: The transaction id from Digital Post. Defaults to None.
            message: The status message to set on the NemSMS message. Defaults to None.
        """
        values = {}
        values["status"] = status
        values["updated_at"] = datetime.now()
        values["status_message"] = message
        if transaction_id:
            values["transaction_id"] = transaction_id

        with connection.get_session() as session:
            q = (
                update(NemSMSMessage)
                .where(NemSMSMessage.id == self.id)
                .values(values)
            )
            session.execute(q)
            session.commit()


def add_messages(shipment_id: str, recipients: list[str]):
    """Add multiple new messages to the database
    based on the list of recipients.

    Args:
        shipment_id: The id of the shipment the messages belong to.
        recipients: A list of recipients.
    """
    message_dicts = []

    for recipient in recipients:
        message_dicts.append(
            {
                "shipment_id": shipment_id,
                "recipient_id": recipient,
            }
        )

    with connection.get_session() as session:
        session.execute(insert(NemSMSMessage), message_dicts)
        session.commit()


def get_messages(shipment_id: str) -> tuple[NemSMSMessage]:
    """Get all messages belonging to a shipment."""
    with connection.get_session() as session:
        query = select(NemSMSMessage).where(NemSMSMessage.shipment_id == shipment_id)
        result = session.execute(query).scalars()
        return tuple(result)


def abort_messages(shipment_id: str, user: str):
    """Set all waiting nemsms-messages in the given shipment to
    aborted. Also add a message about who aborted.

    Args:
        shipment_id: The id of the shipment.
        user: The name of the user who aborted the shipment.
    """
    with connection.get_session() as session:
        query = (
            update(NemSMSMessage)
            .values(
                status=ShipmentStatus.ABORTED,
                status_message=f"Afbrudt af {user}"
            )
            .where(
                NemSMSMessage.shipment_id == shipment_id,
                NemSMSMessage.status == ShipmentStatus.WAITING
            )
        )
        session.execute(query)
        session.commit()
