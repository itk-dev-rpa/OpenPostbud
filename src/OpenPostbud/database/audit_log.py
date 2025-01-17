"""This module contains the AuditLog ORM class."""

from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from OpenPostbud.database.base import Base
from OpenPostbud.database import connection


class AuditLog(Base):
    """An ORM class representing Audit logs"""
    __tablename__ = "AuditLogs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(default=datetime.now)
    user: Mapped[str]
    path: Mapped[str]


def add_log(user: str, path: str):
    """Add a new log to the audit log.

    Args:
        user: The user who visited the path.
        path: The path that was requested.
    """
    log = AuditLog(
        user=user,
        path=path
    )

    with connection.get_session() as session:
        session.add(log)
        session.commit()
