"""This module is contains for the Shipment ORM class."""

from datetime import datetime, timedelta
import logging

from sqlalchemy import String, select, delete
from sqlalchemy.orm import Mapped, mapped_column

from OpenPostbud import config
from OpenPostbud.database.base import Base
from OpenPostbud.database import connection
from OpenPostbud.database.data_types.id_generator import create_id


class NemSMSShipment(Base):
    """An ORM class representing a NemSMS Shipment."""
    __tablename__ = "NemSMS_Shipments"

    id: Mapped[str] = mapped_column(String(13), primary_key=True, default=create_id("NS-", 10))
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(200))
    message_text: Mapped[str] = mapped_column(String(160))
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    created_by: Mapped[str] = mapped_column(String(50))
    deletion_date: Mapped[datetime]

    def to_row_dict(self):
        """Convert to a dictionary to be shown in a table."""
        return {
            "id": str(self.id),
            "name": self.name,
            "created_at": self.created_at.strftime("%d/%m/%Y %H:%M:%S"),
            "created_by": self.created_by,
        }


def add_shipment(name: str, description: str, message_text: str, created_by: str) -> str:
    """Add a new NemSMS Shipment to the database.

    Args:
        name: The name of the shipment.
        description: The description of the shipment.
        message_text: The message text of the shipment.
        created_by: The name of the user who created the shipment.
        template_id: The id of the template connected to the shipment.

    Returns:
        The id of the new shipment.
    """
    shipment = NemSMSShipment(
        name=name,
        description=description,
        message_text=message_text,
        created_by=created_by,
        deletion_date=datetime.today() + timedelta(days=config.SHIPMENT_LIFETIME_DAYS)
    )

    with connection.get_session() as session:
        session.add(shipment)
        session.commit()
        return shipment.id


def get_shipments() -> tuple[NemSMSShipment]:
    """Get all shipments from the database."""
    with connection.get_session() as session:
        result = session.execute(select(NemSMSShipment).order_by(NemSMSShipment.created_at.desc())).scalars()
        return tuple(result)


def get_shipment(shipment_id: str) -> NemSMSShipment | None:
    """Get a single shipment from the database."""
    with connection.get_session() as session:
        return session.get(NemSMSShipment, shipment_id)


def delete_old_shipments():
    """Delete shipments that are older than SHIPMENT_LIFETIME_DAYS.
    Messages are also deleted by database cascade.
    """
    logging.info("Cleaning up old shipments.")

    with connection.get_session() as session:
        query = delete(NemSMSShipment).where(datetime.today() > NemSMSShipment.deletion_date)
        count = session.execute(query).rowcount
        session.commit()

    logging.info(f"Deleted {count} old NemSMS shipments.")
