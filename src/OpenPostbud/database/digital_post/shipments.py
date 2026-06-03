"""This module is contains for the Shipment ORM class."""

from datetime import datetime, timedelta
import logging

from sqlalchemy import String, ForeignKey, select
from sqlalchemy.orm import Mapped, mapped_column

from OpenPostbud import config
from OpenPostbud.database.base import Base
from OpenPostbud.database import connection
from OpenPostbud.database.data_types.id_generator import create_id
from OpenPostbud.database import document_storage


class Shipment(Base):
    """An ORM class representing a Shipment."""
    __tablename__ = "Shipments"

    id: Mapped[str] = mapped_column(String(12), primary_key=True, default=create_id("S-", 10))
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(200))
    template_id: Mapped[int] = mapped_column(ForeignKey("Templates.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    created_by: Mapped[str] = mapped_column(String(50))
    owner_group: Mapped[str] = mapped_column(String)

    def to_row_dict(self):
        """Convert to a dictionary to be shown in a table."""
        return {
            "id": str(self.id),
            "name": self.name,
            "created_at": self.created_at.strftime("%d/%m/%Y %H:%M:%S"),
            "created_by": self.created_by,
        }

    def get_deletion_date(self) -> datetime:
        """Get the deletion date of the shipment."""
        return self.created_at + timedelta(days=config.SHIPMENT_LIFETIME_DAYS)


def add_shipment(name: str, description: str, created_by: str, template_id: int, owner_group: str) -> str:
    """Add a new Shipment to the database.

    Args:
        name: The name of the shipment.
        description: The description of the shipment.
        created_by: The name of the user who created the shipment.
        template_id: The id of the template connected to the shipment.
        owner_group: The group that owns the shipment.

    Returns:
        The id of the new shipment.
    """
    shipment = Shipment(
        name=name,
        description=description,
        template_id=template_id,
        created_by=created_by,
        owner_group=owner_group
    )

    with connection.get_session() as session:
        session.add(shipment)
        session.commit()
        return shipment.id


def get_shipments(groups: list[str] | None = None) -> tuple[Shipment]:
    """Get all shipments from the database.

    Args:
        groups: If given, only shipments owned by one of these groups are
            returned. If None, all shipments are returned (system context).
    """
    with connection.get_session() as session:
        query = select(Shipment).order_by(Shipment.created_at.desc())
        if groups is not None:
            query = query.where(Shipment.owner_group.in_(groups))
        result = session.execute(query).scalars()
        return tuple(result)


def get_shipment(shipment_id: str, groups: list[str] | None = None) -> Shipment | None:
    """Get a single shipment from the database.

    Args:
        shipment_id: The id of the shipment.
        groups: If given, the shipment is only returned if it is owned by one
            of these groups. If None, no ownership check is performed.
    """
    with connection.get_session() as session:
        shipment = session.get(Shipment, shipment_id)
        if shipment is not None and groups is not None and shipment.owner_group not in groups:
            return None
        return shipment


def delete_old_shipments():
    """Delete shipments that are older than SHIPMENT_LIFETIME_DAYS.
    Letters are also deleted by database cascade.
    """
    logging.info("Cleaning up old shipments.")

    with connection.get_session() as session:
        query = select(Shipment).where((datetime.today() - timedelta(days=config.SHIPMENT_LIFETIME_DAYS)) > Shipment.created_at)
        shipments = list(session.execute(query).scalars())

        for shipment in shipments:
            document_storage.delete_shipment_docs(shipment.id)
            session.delete(shipment)

        session.commit()

    logging.info(f"Deleted {len(shipments)} old shipments.")
