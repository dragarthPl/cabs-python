from repair.legacy.job.job_result import JobResult
from repair.legacy.job.repair_job import RepairJob
from repair.legacy.user.employee_driver import EmployeeDriver


class EmployeeDriverWithLeasedCar(EmployeeDriver):
    lasing_company_id: int

    def handle(self, job: RepairJob) -> JobResult:
        return JobResult(JobResult.Decision.REDIRECTION).add_param("shouldHandleBy", self.lasing_company_id)
