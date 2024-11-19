from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from OpenPostbud.database.base import Base
from OpenPostbud.database import connection


class AuditLog(Base):
    __tablename__ = "AuditLogs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(default=datetime.now)
    user: Mapped[str]
    path: Mapped[str]


def add_log(user: str, path: str):
    log = AuditLog(
        user=user,
        path=path
    )

    with connection.get_session() as session:
        session.add(log)
        session.commit()