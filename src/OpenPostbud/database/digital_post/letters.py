from __future__ import annotations

from datetime import datetime
from csv import DictReader
from io import StringIO, BytesIO
import json
from enum import Enum

from mailmerge import MailMerge
from sqlalchemy import ForeignKey, insert, select
from sqlalchemy.orm import Mapped, mapped_column

from OpenPostbud.database.base import Base
from OpenPostbud.database import connection


from OpenPostbud.database.digital_post.templates import Template
from OpenPostbud.database.digital_post.shipments import Shipment
from OpenPostbud.database.encrypted_string import EncryptedString


class LetterStatus(Enum):
    WAITING = "waiting"
    SENDING = "sending"
    SENT = "sent"
    RECEIVED = "received"
    FAILED = "failed"


class Letter(Base):
    __tablename__ = "Letters"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    shipment_id: Mapped[int] = mapped_column(ForeignKey("Shipments.id"))
    recipient_id: Mapped[str] = mapped_column(EncryptedString())
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now)
    status: Mapped[LetterStatus] = mapped_column(default=LetterStatus.WAITING)
    field_data: Mapped[str] = mapped_column(EncryptedString())
    transaction_id: Mapped[str] = mapped_column(nullable=True)

    def to_row_dict(self) -> dict[str, str]:
        return {
            "id": str(self.id),
            "recipient": self.recipient_id,
            "updated_at": self.updated_at.strftime("%d-%m-%Y %H:%M:%S"),
            "status": self.status.value
        }

    def merge_letter(self) -> tuple[bytes, str]:
        """Merge the letter's merge field data with its template.

        Returns:
            The merged docx letter as bytes and the file name.
        """
        template = self.get_letter_template()

        with MailMerge(BytesIO(template.file_data)) as document:
            field_data = json.loads(self.field_data)
            document.merge(**field_data)
            output = BytesIO()
            document.write(output)

        output.seek(0)
        return output.read(), template.file_name

    def get_letter_template(self) -> Template:
        """Get the template associated with this letter.

        Returns:
            The Template object associated with this letter.
        """
        with connection.get_session() as session:
            q = select(Template).join(Shipment).join(Letter).where(Letter.id == self.id)
            return session.execute(q).scalar_one()


def add_letters(shipment_id: int, csv_file: bytes):
    reader = DictReader(StringIO(csv_file.decode()))

    letter_dicts = []

    for line in reader:
        recipient = line["Modtager"]
        del line["Modtager"]
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


def get_letters(shipment_id: int) -> tuple[Letter]:
    with connection.get_session() as session:
        query = select(Letter).where(Letter.shipment_id == shipment_id)
        result = session.execute(query).scalars()
        return tuple(result)
