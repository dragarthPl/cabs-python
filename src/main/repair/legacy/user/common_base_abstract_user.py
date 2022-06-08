from common.base_entity import BaseEntity
from repair.legacy.job.common_base_abstract_job import CommonBaseAbstractJob
from repair.legacy.job.job_result import JobResult
from repair.legacy.job.maintenance_job import MaintenanceJob
from repair.legacy.job.repair_job import RepairJob


class CommonBaseAbstractUser(BaseEntity):
    def do_job(self, job: 'CommonBaseAbstractJob') -> JobResult:
        # poor man's pattern matching
        if isinstance(job, RepairJob):
            return self.handle(job)
        if isinstance(job, MaintenanceJob):
            return self.handle(job)
        return self.default_handler(job)

    def handle(self, job: CommonBaseAbstractJob) -> JobResult:
        return self.default_handler(job)

    def default_handler(self, job: CommonBaseAbstractJob) -> JobResult:
        raise AttributeError(f"{self.__class__.__name__} can not handle {job.__class__.__name__}")
