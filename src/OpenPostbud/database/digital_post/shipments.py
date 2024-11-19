from datetime import datetime

from sqlalchemy import String, ForeignKey, select
from sqlalchemy.orm import Mapped, mapped_column

from OpenPostbud.database.base import Base
from OpenPostbud.database import connection


class Shipment(Base):
    __tablename__ = "Shipments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(200))
    template_id: Mapped[int] = mapped_column(ForeignKey("Templates.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    created_by: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(10), default="waiting")

    def to_row_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.strftime("%d/%m/%Y %H:%M:%S"),
            "created_by": self.created_by,
            "status": self.status
        }


def add_shipment(name: str, description: str, created_by: str, template_id: int) -> int:
    shipment = Shipment(
        name=name,
        description=description,
        template_id=template_id,
        created_by=created_by,
    )

    with connection.get_session() as session:
        session.add(shipment)
        session.commit()
        return shipment.id


def get_shipments() -> tuple[Shipment]:
    with connection.get_session() as session:
        result = session.execute(select(Shipment).order_by(Shipment.id)).scalars()
        return tuple(result)


def get_shipment(shipment_id: int) -> Shipment:
    with connection.get_session() as session:
        return session.get(Shipment, shipment_id)
