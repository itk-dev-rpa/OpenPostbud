"""This module contains the registration worker responsible
for performing registration tasks created in the web application.
It is spawned as a separate process next to the UI process.
"""

import time
from datetime import datetime
import os

import dotenv
from python_serviceplatformen import digital_post
from python_serviceplatformen.authentication import KombitAccess
from sqlalchemy import select, update

from OpenPostbud.database import connection
from OpenPostbud.database.check_registration.registration_task import RegistrationTask, TaskStatus
from OpenPostbud.database.check_registration import registration_job

dotenv.load_dotenv()


def start_process():
    """The entry point of the worker process.

    Raises:
        RuntimeError: If any exception is raised when handling a task.
    """
    cvr = os.environ["cvr"]
    cert_path = os.environ["kombit_cert_path"]
    test = bool(os.environ["Kombit_test_env"])
    sleep_time = float(os.environ["registration_worker_sleep_time"])
    kombit_access = KombitAccess(cvr, cert_path, test=test)

    while True:
        task = get_waiting_task()
        if task:
            try:
                handle_task(task, kombit_access)
            except Exception as e:
                fail_task(task)
                raise RuntimeError("Error during handling of task") from e
        else:
            time.sleep(sleep_time)


def get_waiting_task() -> RegistrationTask | None:
    """Get a registration task that has the status "waiting".
    Set its status to "checking".

    Returns:
        A waiting registration task if any.
    """
    with connection.get_session() as session:
        sub_q = (
            select(RegistrationTask.id)
            .where(RegistrationTask.status == TaskStatus.WAITING)
            .limit(1)
            .scalar_subquery()
        )

        q = (
            update(RegistrationTask)
            .where(RegistrationTask.id == sub_q)
            .values(
                status=TaskStatus.CHECKING,
                updated_at=datetime.now()
            )
            .returning(RegistrationTask)
        )

        task = session.execute(q).scalar()
        if task:
            session.commit()

    return task


def handle_task(task: RegistrationTask, kombit_access: KombitAccess):
    """Handle the registration task looking up registration in the Kombit API.
    Set the result and status to "checked".

    Args:
        task: The task to handle.
        kombit_access: The KombitAccess object to authenticate against the Kombit API.
    """
    job = registration_job.get_registration_job(task.job_id)
    result = digital_post.is_registered(task.registrant_id, job.job_type.value, kombit_access)

    with connection.get_session() as session:
        q = (
            update(RegistrationTask)
            .where(RegistrationTask.id == task.id)
            .values(
                result=result,
                status=TaskStatus.CHECKED,
                updated_at=datetime.now()
            )
        )
        session.execute(q)
        session.commit()


def fail_task(task: RegistrationTask):
    """Mark a task as failed.

    Args:
        task: The task to mark as failed.
    """
    with connection.get_session() as session:
        q = (
            update(RegistrationTask)
            .where(RegistrationTask.id == task.id)
            .values(
                status=TaskStatus.FAILED,
                updated_at=datetime.now()
            )
        )
        session.execute(q)
        session.commit()


if __name__ == '__main__':
    start_process()
