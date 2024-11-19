
from datetime import datetime
from enum import Enum

from sqlalchemy import ForeignKey, insert, select, String
from sqlalchemy.orm import Mapped, mapped_column

from OpenPostbud.database.base import Base
from OpenPostbud.database import connection
from OpenPostbud.database.encrypted_string import EncryptedString


class TaskStatus(Enum):
    WAITING = "waiting"
    CHECKING = "checking"
    CHECKED = "checked"
    FAILED = "failed"


class RegistrationTask(Base):
    __tablename__ = "RegistrationTasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("RegistrationJobs.id"))
    registrant_id: Mapped[str] = mapped_column(EncryptedString())
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now)
    status: Mapped[TaskStatus] = mapped_column(default=TaskStatus.WAITING)
    result: Mapped[bool] = mapped_column(nullable=True)

    def to_row_dict(self) -> dict[str, str]:
        return {
            "id": str(self.id),
            "registrant": self.registrant_id,
            "updated_at": self.updated_at.strftime("%d-%m-%Y %H:%M:%S"),
            "status": self.status.value,
            "result": str(self.result) if self.result is not None else "N/A"
        }


def add_registration_tasks(job_id: int, registrant_list: list[str]):
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
    with connection.get_session() as session:
        query = select(RegistrationTask).where(RegistrationTask.job_id == job_id)
        result = session.execute(query).scalars()
        return tuple(result)
