"""This module contains the Letter ORM class."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
import json
from enum import Enum
import logging
import re

from mailmerge import MailMerge
from sqlalchemy import ForeignKey, insert, select, String, update
from sqlalchemy.orm import Mapped, mapped_column
import requests

from OpenPostbud.database.base import Base
from OpenPostbud.database import connection
from OpenPostbud.database.digital_post.templates import Template
from OpenPostbud.database.digital_post.shipments import Shipment
from OpenPostbud.database.data_types.encrypted_string import EncryptedString
from OpenPostbud.database.data_types.id_generator import create_id


class MessageStatus(Enum):
    """An enum representing a letter's status."""
    WAITING = "Afventer"
    SENDING = "Behandles"
    SENT = "Afsendt"
    DELIVERED = "Leveret"
    FAILED = "Fejlet"


class NemSMSMessage(Base):
    """An ORM class representing a letter."""
    __tablename__ = "NemSMS_Messages"

    id: Mapped[str] = mapped_column(String(13), primary_key=True, default=create_id("NM-", 10))
    shipment_id: Mapped[str] = mapped_column(ForeignKey("NemSMS_Shipments.id", ondelete="CASCADE"))
    recipient_id: Mapped[str] = mapped_column(EncryptedString())
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now)
    status: Mapped[MessageStatus] = mapped_column(default=MessageStatus.WAITING)
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


    def set_status(self, status: MessageStatus, transaction_id: str | None = None, message: str | None = None):
        """Set the status of the letter in the database.
        The transaction id is not overwritten if the given value is None.

        Args:
            status: The status to set on the letter.
            transaction_id: The transaction id from Digital Post. Defaults to None.
            message: The message to set on the letter. Defaults to None.
        """
        values = {}
        values["status"] = status
        values["updated_at"] = datetime.now()
        values["message"] = message
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
    """Add multiple new letters to the database based
    on a csv file containing letter merge data.

    Args:
        shipment_id: The id of the shipment the letters belong to.
        csv_data: A list of dictionaries containing merge data.
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
