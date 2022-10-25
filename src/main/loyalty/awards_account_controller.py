from fastapi_injector import Injected

from loyalty.awards_account_dto import AwardsAccountDTO
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from loyalty.awards_service import AwardsService

awards_account_router = InferringRouter(tags=["AwardsAccountController"])

@cbv(awards_account_router)
class AwardsAccountController:
    awards_service: AwardsService = Injected(AwardsService)

    @awards_account_router.post("/clients/{client_id}/awards", )
    def create(self, client_id: int) -> AwardsAccountDTO:
        self.awards_service.register_to_program(client_id)
        return self.awards_service.find_by(client_id)

    @awards_account_router.post("/clients/{client_id}/awards/activate")
    def activate(self, client_id: int) -> AwardsAccountDTO:
        self.awards_service.activate_account(client_id)
        return self.awards_service.find_by(client_id)

    @awards_account_router.post("/clients/{client_id}/awards/deactivate")
    def deactivate(self, client_id: int) -> AwardsAccountDTO:
        self.awards_service.deactivate_account(client_id)
        return self.awards_service.find_by(client_id)

    @awards_account_router.get("/clients/{client_id}/awards/balance")
    def calculate_balance(self, client_id: int) -> int:
        return self.awards_service.calculate_balance(client_id)

    @awards_account_router.post("/clients/{client_id}/awards/transfer/{to_client_id}/{how_much}")
    def transfer_miles(self, client_id: int, to_client_id: int, how_much: int) -> AwardsAccountDTO:
        self.awards_service.transfer_miles(client_id, to_client_id, how_much)
        return self.awards_service.find_by(client_id)

    @awards_account_router.post("/clients/{client_id}/")
    def find_by(self, client_id: int) -> AwardsAccountDTO:
        return self.awards_service.find_by(client_id)
