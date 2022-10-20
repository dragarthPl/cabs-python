from injector import inject

from repair.legacy.dao.user_dao import UserDAO
from repair.legacy.job.common_base_abstract_job import CommonBaseAbstractJob
from repair.legacy.user.common_base_abstract_user import CommonBaseAbstractUser


class JobDoer:

    user_dao: UserDAO

    @inject
    def __init__(self, user_dao: UserDAO):
        self.user_dao = user_dao  # I'll inject test double some day because it makes total sense to me

    def repair(self, user_id: int, job: CommonBaseAbstractJob):
        user: CommonBaseAbstractUser = self.user_dao.get_one(user_id)
        return user.do_job(job)

    def repair_2_parallel_models(self, user_id: int, job: CommonBaseAbstractJob):
        user: CommonBaseAbstractUser = self.user_dao.get_one(user_id)
        return user.do_job(job)
