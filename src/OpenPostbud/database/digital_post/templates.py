from io import BytesIO
import json

from mailmerge import MailMerge
from sqlalchemy import String, select
from sqlalchemy.orm import Mapped, mapped_column

from OpenPostbud.database.base import Base
from OpenPostbud.database import connection


class Template(Base):
    __tablename__ = "Templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    file_name: Mapped[str] = mapped_column(String(100))
    file_data: Mapped[bytes]
    field_names: Mapped[str]


def add_template(file_name: str, file_data: bytes) -> int:
    file = BytesIO(file_data)
    with MailMerge(file) as document:
        field_names = sorted(list(document.get_merge_fields()))

    template = Template(
        file_name=file_name,
        file_data = file_data,
        field_names=json.dumps(field_names)
    )

    with connection.get_session() as session:
        session.add(template)
        session.commit()
        return template.id


def get_template_name(template_id: int) -> str:
    with connection.get_session() as session:
        return session.execute(select(Template.file_name).where(Template.id == template_id)).scalar()


def get_template(template_id: int) -> Template:
    with connection.get_session() as session:
        return session.get(Template, template_id)
