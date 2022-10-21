from fastapi_injector import Injected

from agreements.contract_attachment_dto import ContractAttachmentDTO
from dto.contract_dto import ContractDTO
from agreements.contract import Contract
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from service.contract_service import ContractService

contract_router = InferringRouter(tags=["ContractController"])

@cbv(contract_router)
class ContractController:
    contract_service: ContractService = Injected(ContractService)

    @contract_router.post("/contracts/")
    def create(self, contract_dto: ContractDTO) -> ContractDTO:
        created: Contract = self.contract_service.create_contract(contract_dto)
        return ContractDTO(contract=created)

    @contract_router.get("/contracts/{contract_id}")
    def find(self, contract_id: int) -> ContractDTO:
        contract: Contract = self.contract_service.find_dto(contract_id)
        return ContractDTO(contract=contract)

    @contract_router.post("/contracts/{contract_id}/attachment")
    def propose_attachment(self, contract_id: int, contract_attachment_dto: ContractAttachmentDTO) -> ContractDTO:
        dto = self.contract_service.propose_attachment(contract_id, contract_attachment_dto)
        return dto

    @contract_router.post("/contracts/{contract_id}/attachment/{attachment_id}/reject")
    def reject_attachment(self, contract_id: int, attachment_id: int) -> dict:
        self.contract_service.reject_attachment(attachment_id)
        return {}

    @contract_router.post("/contracts/{contract_id}/attachment/{attachment_id}/accept")
    def accept_attachment(self, contract_id: int, attachment_id: int) -> dict:
        self.contract_service.accept_attachment(contract_id, attachment_id)
        return {}

    @contract_router.delete("/contracts/{contract_id}/attachment/{attachment_id}")
    def remove_attachment(self, contract_id: int, attachment_id: int) -> dict:
        self.contract_service.remove_attachment(attachment_id)
        return {}

    @contract_router.get("/contracts/{contract_id}/accept")
    def accept_contract(self, contract_id: int) -> dict:
        self.contract_service.accept_contract(contract_id)
        return {}

    @contract_router.get("/contracts/{contract_id}/reject")
    def reject_contract(self, contract_id: int) -> dict:
        self.contract_service.reject_contract(contract_id)
        return {}
