from fastapi import Depends

from entity import Client
from service.awards_service import AwardsService, AwardsServiceImpl


class AwardsAccountFixture:
    awards_service: AwardsService

    def __init__(self, awards_service: AwardsService = Depends(AwardsServiceImpl)):
        self.awards_service = awards_service

    def awards_account(self, client: Client):
        self.awards_service.register_to_program(client.id)

    def active_awards_account(self, client: Client):
        self.awards_account(client)
        self.awards_service.activate_account(client.id)
