"""This module contains ORM classes representing registration jobs."""

from datetime import datetime, timedelta
from enum import Enum
import logging

from sqlalchemy import select, String, delete
from sqlalchemy.orm import Mapped, mapped_column

from OpenPostbud import config
from OpenPostbud.database.base import Base
from OpenPostbud.database import connection
from OpenPostbud.database.data_types.id_generator import create_id


class JobType(Enum):
    """A enum used to denote the type of a registration job."""
    NEMSMS = "nemsms"
    DIGITAL_POST = "digitalpost"


# We don't care about duplicate code for ORM classes.
# pylint: disable=duplicate-code
class RegistrationJob(Base):
    """An ORM class representing a registration job.
    A job is a collection of multiple tasks.
    """
    __tablename__ = "RegistrationJobs"

    id: Mapped[str] = mapped_column(String(12), primary_key=True, default=create_id("J-", 10))
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(200))
    job_type: Mapped[JobType]
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    created_by: Mapped[str] = mapped_column(String(50))
    owner_group: Mapped[str] = mapped_column(String)

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

    def get_deletion_date(self) -> datetime:
        """Get the deletion date of the job."""
        return self.created_at + timedelta(days=config.REGISTRATION_JOB_LIFETIME_DAYS)
# pylint: enable=duplicate-code


def add_registation_job(name: str, description: str, job_type: JobType, created_by: str, owner_group: str) -> str:
    """Add a new registration job to the database.

    Args:
        name: The name of the job.
        description: The description of the job.
        job_type: The type of the job.
        created_by: The username of the creator.
        owner_group: The group that owns the job.

    Returns:
        The id of the newly created job.
    """
    job = RegistrationJob(
        name=name,
        description=description,
        job_type=job_type,
        created_by=created_by,
        owner_group=owner_group
    )

    with connection.get_session() as session:
        session.add(job)
        session.commit()
        return job.id


def get_registration_jobs(groups: list[str] | None = None) -> tuple[RegistrationJob]:
    """Get all registration jobs from the database.

    Args:
        groups: If given, only jobs owned by one of these groups are returned.
            If None, all jobs are returned (system context).
    """
    with connection.get_session() as session:
        query = select(RegistrationJob).order_by(RegistrationJob.id)
        if groups is not None:
            query = query.where(RegistrationJob.owner_group.in_(groups))
        result = session.execute(query).scalars()
        return tuple(result)


def get_registration_job(job_id: int, groups: list[str] | None = None) -> RegistrationJob | None:
    """Get a single registration job from the database.

    Args:
        job_id: The id of the job.
        groups: If given, the job is only returned if it is owned by one of
            these groups. If None, no ownership check is performed.
    """
    with connection.get_session() as session:
        job = session.get(RegistrationJob, job_id)
        if job is not None and groups is not None and job.owner_group not in groups:
            return None
        return job


def delete_old_registration_jobs():
    """Delete registration jobs that are older than REGISTRATION_JOB_LIFETIME_DAYS.
    Tasks are also deleted by database cascade.
    """
    logging.info("Cleaning up old registration jobs.")

    with connection.get_session() as session:
        query = delete(RegistrationJob).where((datetime.today() - timedelta(days=config.REGISTRATION_JOB_LIFETIME_DAYS)) > RegistrationJob.created_at)
        count = session.execute(query).rowcount
        session.commit()

    logging.info(f"Deleted {count} old registration jobs.")
