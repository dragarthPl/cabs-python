from typing import Set
from unittest import TestCase

from fastapi.params import Depends

from core.database import create_db_and_tables, drop_db_and_tables
from money import Money
from repair.legacy.job.job_result import JobResult
from repair.legacy.job.repair_job import RepairJob
from repair.legacy.parts.parts import Parts
from repair.legacy.service.job_doer import JobDoer
from tests.common.fixtures import DependencyResolver

dependency_resolver = DependencyResolver()


class TestJobDoer(TestCase):

    ANY_USER: int = 1

    job_doer: JobDoer = dependency_resolver.resolve_dependency(
        Depends(JobDoer)
    )

    def setUp(self):
        create_db_and_tables()

    def test_employee_with_own_car_with_warranty_should_have_covered_all_parts_for_free(self):
        result: JobResult = self.job_doer.repair(self.ANY_USER, self.repair_job())

        self.assertEqual(result.decision, JobResult.Decision.ACCEPTED)
        self.assertEqual(result.params.get("acceptedParts"), self.all_parts())
        self.assertEqual(result.params.get("totalCost"), Money.ZERO)

    def repair_job(self) -> RepairJob:
        job: RepairJob = RepairJob()
        job.parts_to_repair = self.all_parts()
        job.estimated_value = Money(7000)
        return job

    def all_parts(self) -> Set[Parts]:
        return set(Parts)

    def tearDown(self) -> None:
        drop_db_and_tables()
