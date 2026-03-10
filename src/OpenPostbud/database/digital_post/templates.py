"""This module contains the Template ORM class."""

import json
from functools import lru_cache

from sqlalchemy import String, select
from sqlalchemy.orm import Mapped, mapped_column

from OpenPostbud.database.base import Base
from OpenPostbud.database import connection
from OpenPostbud.database.digital_post.shipments import Shipment
from OpenPostbud.utils import docx_util


class Template(Base):
    """An ORM class representing a letter template."""
    __tablename__ = "Templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    file_name: Mapped[str] = mapped_column(String(100))
    file_data: Mapped[bytes]
    field_names: Mapped[str]


def add_template(file_name: str, file_data: bytes) -> int:
    """Add a new template to the database.

    Args:
        file_name: The name of the template file.
        file_data: The bytes of the file.

    Returns:
        The id of the new template.
    """
    if file_name.endswith(".docx"):
        field_names = docx_util.get_merge_fields(file_data)
    else:
        field_names = []

    template = Template(
        file_name=file_name,
        file_data=file_data,
        field_names=json.dumps(field_names)
    )

    with connection.get_session() as session:
        session.add(template)
        session.commit()
        return template.id


def get_template_name(template_id: int) -> str:
    """Get the name of a template in the database."""
    with connection.get_session() as session:
        return session.execute(select(Template.file_name).where(Template.id == template_id)).scalar()


def get_template(template_id: int) -> Template:
    """Get a template from the database."""
    with connection.get_session() as session:
        return session.get(Template, template_id)


@lru_cache(maxsize=2)
def get_template_by_shipment(shipment_id: str) -> Template:
    """Get the template for the shipment with the given id.

    Args:
        shipment_id: The id of the shipment to get the template for.

    Returns:
        The shipment's template.
    """
    with connection.get_session() as session:
        q = select(Template).join(Shipment).where(Shipment.id == shipment_id)
        return session.execute(q).scalar_one()
