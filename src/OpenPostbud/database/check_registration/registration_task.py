"""This module contains ORM classes representing registration tasks."""

from datetime import datetime
from enum import Enum

from sqlalchemy import ForeignKey, insert, select
from sqlalchemy.orm import Mapped, mapped_column

from OpenPostbud.database.base import Base
from OpenPostbud.database import connection
from OpenPostbud.database.encrypted_string import EncryptedString


class TaskStatus(Enum):
    """An enum denoting the status of a task."""
    WAITING = "waiting"
    CHECKING = "checking"
    CHECKED = "checked"
    FAILED = "failed"


class RegistrationTask(Base):
    """An ORM class representing a singular registration task.
    A registration task corresponds to a single lookup of a person.
    """
    __tablename__ = "RegistrationTasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("RegistrationJobs.id"))
    registrant_id: Mapped[str] = mapped_column(EncryptedString())
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now)
    status: Mapped[TaskStatus] = mapped_column(default=TaskStatus.WAITING)
    result: Mapped[bool] = mapped_column(nullable=True)

    def to_row_dict(self) -> dict[str, str]:
        """Convert to a dictionary to be shown in a table."""
        return {
            "id": str(self.id),
            "registrant": f"{self.registrant_id[:6]}-{self.registrant_id[6:]}",
            "updated_at": self.updated_at.strftime("%d-%m-%Y %H:%M:%S"),
            "status": self.status.value,
            "result": str(self.result) if self.result is not None else "N/A"
        }


def add_registration_tasks(job_id: int, registrant_list: list[str]):
    """Add multiple new tasks to the database based on the given list.
    One task will be added for each CPR number in the list.

    Args:
        job_id: The job the tasks belong to.
        registrant_list: A list of CPR numbers.
    """
    task_dicts = []

    for registrant in registrant_list:
        task_dicts.append(
            {
                "job_id": job_id,
                "registrant_id": registrant,
            }
        )

    with connection.get_session() as session:
        session.execute(insert(RegistrationTask), task_dicts)
        session.commit()


def get_registration_tasks(job_id: int) -> tuple[RegistrationTask]:
    """Get all tasks belonging to the given job."""
    with connection.get_session() as session:
        query = select(RegistrationTask).where(RegistrationTask.job_id == job_id)
        result = session.execute(query).scalars()
        return tuple(result)
