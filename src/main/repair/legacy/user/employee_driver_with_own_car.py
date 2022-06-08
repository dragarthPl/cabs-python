from typing import Set, Optional

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlmodel import Field, Relationship

from money import Money
from repair.legacy.job.job_result import JobResult
from repair.legacy.job.repair_job import RepairJob
from repair.legacy.parts.parts import Parts
from repair.legacy.user.employee_driver import EmployeeDriver
from repair.legacy.user.signed_contract import SignedContract


class EmployeeDriverWithOwnCar(EmployeeDriver, table=True):
    __table_args__ = {'extend_existing': True}

    #@OneToOne
    contract_id: Optional[int] = Field(sa_column=Column(Integer, ForeignKey('signedcontract.id')))
    contract: Optional[SignedContract] = Relationship(
        sa_relationship=relationship(
            "repair.legacy.user.signed_contract.SignedContract",
            backref=backref("employeedriverwithowncar", uselist=False)
        )
    )

    # @Column(nullable = false)

    def handle(self, job: RepairJob) -> JobResult:
        accepted_parts: Set[Parts] = set(job.parts_to_repair)
        accepted_parts.intersection_update(self.contract.covered_parts)

        covered_cost: Money = job.estimated_value.percentage_float(self.contract.coverage_ratio)
        total_cost: Money = job.estimated_value.subtract(covered_cost)

        return JobResult(
            JobResult.Decision.ACCEPTED
        ).add_param(
            "totalCost", total_cost
        ).add_param(
            "acceptedParts", accepted_parts
        )
