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

dotenv.load_dotenv(override=True)

SLEEP_TIME = float(os.environ["registration_worker_sleep_time"])


def start_process():
    cvr = os.environ["cvr"]
    cert_path = os.environ["kombit_cert_path"]
    test = bool(os.environ["Kombit_test_env"])
    kombit_access = KombitAccess(cvr, cert_path, test=test)

    while True:
        task = get_waiting_task()
        if task:
            print("Hop")
            try:
                handle_task(task, kombit_access)
            except Exception as e:
                fail_task(task)
                raise e
        else:
            print(f"Sleeping {SLEEP_TIME}")
            time.sleep(SLEEP_TIME)


def get_waiting_task() -> RegistrationTask | None:
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
