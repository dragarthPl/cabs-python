from repair.legacy.dao.user_dao import UserDAO
from repair.legacy.job.common_base_abstract_job import CommonBaseAbstractJob
from repair.legacy.job.job_result import JobResult
from repair.legacy.job.repair_job import RepairJob
from repair.legacy.user.common_base_abstract_user import CommonBaseAbstractUser


class JobDoerParalellModels:
    user_dao: UserDAO
    repair_process: RepairProcess

    def __init__(self, user_dao: UserDAO):
        self.user_dao = user_dao  # I'll inject test double some day because it makes total sense to me

    def repair(self, user_id: int, job: CommonBaseAbstractJob):
        user: CommonBaseAbstractUser = self.user_dao.get_one(user_id)
        return user.do_job(job)

    def repair_2_parallel_models(self, user_id: int, job: CommonBaseAbstractJob):
        # legacy model
        user: CommonBaseAbstractUser = self.user_dao.get_one(user_id)
        job_result: JobResult = user.do_job(job)

        # new model
        new_result = self.run_parallel_model(user_id, job)

        self.compare(new_result, job_result)

        return job_result

    def run_parallel_model(self, user_id: int, job: RepairJob) -> ResolveResult:
        vehicle: PartyId = self.find_vehicle_for(user_id)
        repair_request: RepairRequest = RepairRequest(vehicle, job.parts_to_repair)
        return self.repair_process

    def find_vehicle_for(self, user_id: int) -> PartyId:
        # TODO search in graph
        return PartyId()

    def compare(self, resolve_result: ResolveResult, job_result: JobResult) -> None:
        assert (
            resolve_result.status == ResolveResult.Status.SUCCESS
            and job_result.decision == JobResult.Decision.ACCEPTED
        ) or (
            resolve_result.status == ResolveResult.Status.ERROR
            and job_result.decision == JobResult.Decision.ERROR
        )
        # TODO
