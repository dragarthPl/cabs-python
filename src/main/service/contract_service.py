from dto.contract_attachment_dto import ContractAttachmentDTO
from dto.contract_dto import ContractDTO
from entity import Contract
from entity import ContractAttachment
from fastapi import Depends
from repository.contract_attachment_repository import \
    ContractAttachmentRepositoryImp
from repository.contract_repository import ContractRepositoryImp


class ContractService:
    contract_repository: ContractRepositoryImp
    contract_attachment_repository: ContractAttachmentRepositoryImp

    def __init__(
            self,
            contract_repository: ContractRepositoryImp = Depends(ContractRepositoryImp),
            contract_attachment_repository: ContractAttachmentRepositoryImp = Depends(ContractAttachmentRepositoryImp)
    ):
        self.contract_repository = contract_repository
        self.contract_attachment_repository = contract_attachment_repository

    def create_contract(self, contract_dto: ContractDTO) -> Contract:
        partner_contracts_count = len(self.contract_repository.find_by_partner_name(contract_dto.partner_name)) + 1
        contract = Contract(
            partner_name=contract_dto.partner_name,
            subject=contract_dto.subject,
            contract_no="C/" + str(partner_contracts_count) + "/" + contract_dto.partner_name
        )
        return self.contract_repository.save(contract)

    def accept_contract(self, contract_id: int):
        contract = self.find(contract_id)
        contract.accept()
        self.contract_repository.save(contract)

    def reject_contract(self, contract_id: int):
        contract = self.find(contract_id)
        contract.reject()
        self.contract_repository.save(contract)

    def reject_attachment(self, attachment_id: int) -> None:
        contract: Contract = self.contract_repository.find_by_attachment_id(attachment_id)
        contract.reject_attachment(attachment_id)
        self.contract_repository.save(contract)

    def accept_attachment(self, attachment_id: int):
        contract: Contract = self.contract_repository.find_by_attachment_id(attachment_id)
        contract.accept_attachment(attachment_id)
        self.contract_repository.save(contract)

    def find(self, contract_id: int):
        contract = self.contract_repository.get_one(contract_id)
        if contract is None:
            raise AttributeError("Contract does not exist")
        return contract

    def find_dto(self, contract_id: int):
        return ContractDTO(
            contract=self.find(contract_id),
            attachments=self.contract_attachment_repository.find_by_contract_id(contract_id)
        )

    def propose_attachment(self, contract_id: int, contract_attachment_dto: ContractAttachmentDTO):
        contract = self.find(contract_id)
        contract_attachment = contract.propose_attachment(contract_attachment_dto.data)
        return ContractAttachmentDTO(
            **self.contract_attachment_repository.save(contract_attachment).dict()
        )

    def remove_attachment(self, contract_id: int, attachment_id: int):
        # //TODO sprawdzenie czy nalezy do kontraktu (JIRA: II-14455)
        self.contract_attachment_repository.delete_by_id(attachment_id)


