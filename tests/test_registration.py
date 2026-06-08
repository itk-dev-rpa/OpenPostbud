"""Tests for the check-registration data layer: jobs, tasks, cleanup and cascade."""

import unittest
from datetime import datetime, timedelta

from OpenPostbud import config
from OpenPostbud.database import connection
from OpenPostbud.database.check_registration import registration_job, registration_task
from OpenPostbud.database.check_registration.registration_job import JobType, RegistrationJob
from OpenPostbud.database.check_registration.registration_task import TaskStatus
from tests.db_test_case import DBTestCase


def _make_job(name="Job", owner_group="GroupA", job_type=JobType.NEMSMS) -> str:
    return registration_job.add_registation_job(
        name=name,
        description="desc",
        job_type=job_type,
        created_by="tester",
        owner_group=owner_group,
    )


def _set_created_at(job_id: str, created_at: datetime):
    with connection.get_session() as session:
        job = session.get(RegistrationJob, job_id)
        job.created_at = created_at
        session.commit()


class RegistrationJobTest(DBTestCase):
    def test_add_and_get_job(self):
        job_id = _make_job(name="Lookup", job_type=JobType.DIGITAL_POST)

        job = registration_job.get_registration_job(job_id)

        self.assertTrue(job_id.startswith("J-"))
        self.assertEqual(job.name, "Lookup")
        self.assertEqual(job.job_type, JobType.DIGITAL_POST)

    def test_get_jobs_filters_by_group(self):
        _make_job(name="A", owner_group="GroupA")
        _make_job(name="B", owner_group="GroupB")

        result = registration_job.get_registration_jobs(groups=["GroupA"])

        self.assertEqual({j.name for j in result}, {"A"})

    def test_get_jobs_none_returns_all(self):
        _make_job(owner_group="GroupA")
        _make_job(owner_group="GroupB")

        self.assertEqual(len(registration_job.get_registration_jobs(groups=None)), 2)

    def test_get_job_ownership_check(self):
        job_id = _make_job(owner_group="GroupA")

        self.assertIsNone(registration_job.get_registration_job(job_id, groups=["GroupB"]))
        self.assertIsNotNone(registration_job.get_registration_job(job_id, groups=["GroupA"]))

    def test_delete_old_jobs_cascades_to_tasks(self):
        old_id = _make_job(name="old")
        recent_id = _make_job(name="recent")
        registration_task.add_registration_tasks(old_id, ["1111111111"])
        _set_created_at(
            old_id,
            datetime.now() - timedelta(days=config.REGISTRATION_JOB_LIFETIME_DAYS + 1),
        )

        registration_job.delete_old_registration_jobs()

        remaining = registration_job.get_registration_jobs()
        self.assertEqual({j.id for j in remaining}, {recent_id})
        self.assertEqual(len(registration_task.get_registration_tasks(old_id)), 0)


class RegistrationTaskTest(DBTestCase):
    def test_add_tasks_defaults(self):
        job_id = _make_job()
        registration_task.add_registration_tasks(job_id, ["1111111111", "2222222222"])

        tasks = registration_task.get_registration_tasks(job_id)

        self.assertEqual(len(tasks), 2)
        self.assertTrue(all(t.id.startswith("T-") for t in tasks))
        self.assertTrue(all(t.status == TaskStatus.WAITING for t in tasks))
        self.assertTrue(all(t.result is None for t in tasks))
        # registrant_id is encrypted at rest but decrypts back to the input.
        self.assertEqual({t.registrant_id for t in tasks}, {"1111111111", "2222222222"})

    def test_get_tasks_scoped_to_job(self):
        job_a = _make_job(name="A")
        job_b = _make_job(name="B")
        registration_task.add_registration_tasks(job_a, ["1111111111"])
        registration_task.add_registration_tasks(job_b, ["2222222222"])

        result = registration_task.get_registration_tasks(job_a)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].registrant_id, "1111111111")


class RegistrationModelMethodTest(unittest.TestCase):
    """Pure model methods, no database."""

    def test_job_to_row_dict(self):
        job = RegistrationJob(
            id="J-abc",
            name="Lookup",
            description="d",
            job_type=JobType.NEMSMS,
            created_at=datetime(2024, 3, 9, 14, 30, 0),
            created_by="tester",
        )

        row = job.to_row_dict()

        self.assertEqual(row["id"], "J-abc")
        self.assertEqual(row["job_type"], "nemsms")
        self.assertEqual(row["created_at"], "09-03-2024 14:30:00")

    def test_job_deletion_date(self):
        created = datetime(2024, 1, 1, 12, 0, 0)
        job = RegistrationJob(created_at=created)

        expected = created + timedelta(days=config.REGISTRATION_JOB_LIFETIME_DAYS)
        self.assertEqual(job.get_deletion_date(), expected)

    def test_task_to_row_dict_translates_status_and_result(self):
        from OpenPostbud.database.check_registration.registration_task import RegistrationTask

        task = RegistrationTask(
            id="T-abc",
            registrant_id="1234567890",
            updated_at=datetime(2024, 3, 9, 14, 30, 0),
            status=TaskStatus.CHECKED,
            result=True,
        )

        row = task.to_row_dict()

        self.assertEqual(row["status"], "Færdig")
        self.assertEqual(row["result"], "Tilmeldt")


if __name__ == "__main__":
    unittest.main()
