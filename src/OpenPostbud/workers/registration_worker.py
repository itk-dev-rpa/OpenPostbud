"""This module contains the registration worker responsible
for performing registration tasks created in the web application.
It is spawned as a separate process next to the UI process.
"""

import time
from datetime import datetime
import logging

from python_serviceplatformen import digital_post
from python_serviceplatformen.authentication import KombitAccess
from sqlalchemy import select, update

from OpenPostbud import config
from OpenPostbud.database import connection
from OpenPostbud.database.check_registration.registration_task import RegistrationTask, TaskStatus
from OpenPostbud.database.check_registration import registration_job

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(asctime)s: %(message)s")
logger = logging.getLogger("Registration Worker")


def start_process():
    """The entry point of the worker process.

    Raises:
        RuntimeError: If any exception is raised when handling a task.
    """
    kombit_access = KombitAccess(config.CVR, config.KOMBIT_CERT_PATH, test=config.KOMBIT_TEST_ENV)

    logger.info("Registration worker started.")

    while True:
        task = get_waiting_task()
        if task:
            try:
                logger.info(f"Starting task {task.id}")
                handle_task(task, kombit_access)
                logger.info(f"Task done {task.id}")
            except Exception as e:
                fail_task(task)
                logger.error(f"Task failed {task.id}: {e}")
        else:
            logger.info(f"Sleeping for {config.REGISTRATION_WORKER_SLEEP_TIME} seconds")
            time.sleep(config.REGISTRATION_WORKER_SLEEP_TIME)


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
