"""This module contains ORM classes representing registration jobs."""

from datetime import datetime
from enum import Enum

from sqlalchemy import select, String
from sqlalchemy.orm import Mapped, mapped_column

from OpenPostbud.database.base import Base
from OpenPostbud.database import connection


class JobType(Enum):
    """A enum used to denote the type of a registration job."""
    NEMSMS = "nemsms"
    DIGITAL_POST = "digitalpost"


class RegistrationJob(Base):
    """An ORM class representing a registration job.
    A job is a collection of multiple tasks.
    """
    __tablename__ = "RegistrationJobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(200))
    job_type: Mapped[JobType]
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    created_by: Mapped[str] = mapped_column(String(50))

    def to_row_dict(self) -> dict[str, str]:
        """Convert to a dictionary to be shown in a table."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "job_type": self.job_type.value,
            "created_at": self.created_at.strftime("%d-%m-%Y %H:%M:%S"),
            "created_by": self.created_by
        }


def add_registation_job(name: str, description: str, job_type: JobType, created_by: str) -> int:
    """Add a new registration job to the database.

    Args:
        name: _description_
        description: _description_
        job_type: _description_
        created_by: _description_

    Returns:
        _description_
    """
    job = RegistrationJob(
        name=name,
        description=description,
        job_type=job_type,
        created_by=created_by,
    )

    with connection.get_session() as session:
        session.add(job)
        session.commit()
        return job.id


def get_registration_jobs() -> tuple[RegistrationJob]:
    """Get all registration jobs from the database."""
    with connection.get_session() as session:
        result = session.execute(select(RegistrationJob).order_by(RegistrationJob.id)).scalars()
        return tuple(result)


def get_registration_job(job_id: int) -> RegistrationJob:
    """Get a single registration job from the database."""
    with connection.get_session() as session:
        return session.get(RegistrationJob, job_id)
