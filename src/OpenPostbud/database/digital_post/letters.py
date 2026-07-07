"""This module contains the Letter ORM class."""

from __future__ import annotations

from datetime import datetime
import json
from enum import Enum
import re

from sqlalchemy import ForeignKey, insert, select, String, update
from sqlalchemy.orm import Mapped, mapped_column

from OpenPostbud.database.base import Base
from OpenPostbud.database import connection
from OpenPostbud.database.data_types.encrypted_string import EncryptedString
from OpenPostbud.database.data_types.id_generator import create_id
from OpenPostbud.database.common import ShipmentStatus, PostType
from OpenPostbud.database.digital_post import templates
from OpenPostbud.database import document_storage
from OpenPostbud.utils import docx_util


class MemoFields(Enum):
    """An enum class defining the special fields used for
    Memo functionality.
    a MemoField has the following members:
        key: The name of the field when loaded from merge data.
        mandatory_digital: Whether the field is mandatory when sending Digital Post.
        mandatory_physical: Whether the field is mandatory when sending Fysisk Post.
        pattern: The regex pattern for the field's value.
    """
    def __init__(self, key: str, mandatory_digital: bool, mandatory_physical: bool, pattern: str):
        self.key = key
        self.mandatory_digital = mandatory_digital
        self.mandatory_physical = mandatory_physical
        self.pattern = re.compile(pattern)

    MEMO_MODTAGER = ("Memo Modtager", True, True, r"\d{10}|\d{8}")
    MEMO_LABEL = ("Memo Label", True, False, r"\S.*")

    def is_mandatory_for(self, post_type: PostType) -> bool:
        """Whether this field is mandatory for the given post type.

        AUTO requires the field if it is mandatory for either route, so the
        letter can be sent successfully whichever route a recipient takes.
        """
        if post_type == PostType.DIGITAL:
            return self.mandatory_digital
        if post_type == PostType.PHYSICAL:
            return self.mandatory_physical
        return self.mandatory_digital or self.mandatory_physical


class Letter(Base):
    """An ORM class representing a letter."""
    __tablename__ = "Letters"

    id: Mapped[str] = mapped_column(String(12), primary_key=True, default=create_id("L-", 10))
    shipment_id: Mapped[str] = mapped_column(ForeignKey("Shipments.id", ondelete="CASCADE"))
    recipient_id: Mapped[str] = mapped_column(EncryptedString())
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now)
    status: Mapped[ShipmentStatus] = mapped_column(default=ShipmentStatus.WAITING)
    message: Mapped[str] = mapped_column(String(100), nullable=True)
    field_data: Mapped[str] = mapped_column(EncryptedString())
    transaction_id: Mapped[str] = mapped_column(nullable=True)
    sent_as: Mapped[PostType] = mapped_column(nullable=True)

    def to_row_dict(self) -> dict[str, str]:
        """Convert to a dictionary to be shown in a table."""
        return {
            "id": str(self.id),
            "recipient": self.recipient_id,
            "updated_at": self.updated_at.strftime("%d/%m/%Y %H:%M:%S"),
            "status": self.status.value,
            "message": self.message,
            "sent_as": self.sent_as.value if self.sent_as else ""
        }

    def merge_letter(self) -> bytes:
        """Merge the letter's merge field data with its template
        and convert to pdf.

        Returns:
            The merged pdf letter as bytes.
        """
        stored_file = document_storage.get_letter_doc(self.shipment_id, self.id)
        if stored_file:
            return stored_file

        template = templates.get_template_by_shipment(self.shipment_id)

        if template.file_name.endswith(".docx"):
            field_data = json.loads(self.field_data)
            word_file = docx_util.merge_word_file(template.file_data, field_data)
            pdf_file = docx_util.convert_word_to_pdf(word_file)
            document_storage.save_letter_doc(self.shipment_id, self.id, pdf_file)
            return pdf_file

        return template.file_data

    def set_status(self, status: ShipmentStatus, transaction_id: str | None = None, message: str | None = None, sent_as: PostType | None = None):
        """Set the status of the letter in the database.
        The transaction id and sent_as are not overwritten if the given value is None.

        Args:
            status: The status to set on the letter.
            transaction_id: The transaction id from Digital Post. Defaults to None.
            message: The message to set on the letter. Defaults to None.
            sent_as: The post type the letter was actually sent as. Defaults to None.
        """
        values = {}
        values["status"] = status
        values["updated_at"] = datetime.now()
        values["message"] = message
        if transaction_id:
            values["transaction_id"] = transaction_id
        if sent_as:
            values["sent_as"] = sent_as

        with connection.get_session() as session:
            q = (
                update(Letter)
                .where(Letter.id == self.id)
                .values(values)
            )
            session.execute(q)
            session.commit()


def add_letters(shipment_id: str, csv_data: list[dict[str, str]]):
    """Add multiple new letters to the database based
    on a csv file containing letter merge data.

    Args:
        shipment_id: The id of the shipment the letters belong to.
        csv_data: A list of dictionaries containing merge data.
    """
    letter_dicts = []

    for line in csv_data:
        recipient = line[MemoFields.MEMO_MODTAGER.key]
        del line[MemoFields.MEMO_MODTAGER.key]
        letter_dicts.append(
            {
                "shipment_id": shipment_id,
                "recipient_id": recipient,
                "field_data": json.dumps(line)
            }
        )

    with connection.get_session() as session:
        session.execute(insert(Letter), letter_dicts)
        session.commit()


def get_letters(shipment_id: str) -> tuple[Letter]:
    """Get all letters belonging to a shipment."""
    with connection.get_session() as session:
        query = select(Letter).where(Letter.shipment_id == shipment_id)
        result = session.execute(query).scalars()
        return tuple(result)


def abort_letters(shipment_id: str, user: str):
    """Set all waiting letters in the given shipment to
    aborted. Also add a message about who aborted.

    Args:
        shipment_id: The id of the shipment.
        user: The name of the user who aborted the shipment.
    """
    with connection.get_session() as session:
        query = (
            update(Letter)
            .values(
                status=ShipmentStatus.ABORTED,
                message=f"Afbrudt af {user}"
            )
            .where(
                Letter.shipment_id == shipment_id,
                Letter.status == ShipmentStatus.WAITING
            )
        )
        session.execute(query)
        session.commit()
