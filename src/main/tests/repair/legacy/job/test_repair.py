from typing import Set
from unittest import TestCase

from money import Money
from repair.legacy.job.job_result import JobResult
from repair.legacy.job.repair_job import RepairJob
from repair.legacy.parts.parts import Parts
from repair.legacy.user.employee_driver_with_own_car import EmployeeDriverWithOwnCar
from repair.legacy.user.signed_contract import SignedContract


class TestRepair(TestCase):

    def test_employee_driver_with_own_car_covered_by_warranty_should_repair_for_free(self):
        # given
        employee: EmployeeDriverWithOwnCar = EmployeeDriverWithOwnCar()
        employee.contract = self.full_coverage_warranty()
        # when
        result: JobResult = employee.do_job(self.full_repair())
        # then
        self.assertEqual(JobResult.Decision.ACCEPTED, result.decision)
        self.assertEqual(Money.ZERO, result.params.get("totalCost"))
        self.assertEqual(self.all_parts(), result.params.get("acceptedParts"))

    def full_repair(self):
        job: RepairJob = RepairJob()
        job.estimated_value = Money(50000)
        job.parts_to_repair = self.all_parts()
        return job

    def full_coverage_warranty(self) -> SignedContract:
        contract: SignedContract = SignedContract()
        contract.coverage_ratio = 100.0
        contract.covered_parts = self.all_parts()
        return contract

    def all_parts(self) -> Set[Parts]:
        return set(Parts)
