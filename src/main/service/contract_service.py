from dto.contract_attachment_dto import ContractAttachmentDTO
from dto.contract_dto import ContractDTO
from entity import Contract
from entity.contract_attachment import ContractAttachment
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
        contract = Contract()
        contract.partner_name = contract_dto.partner_name
        partner_contracts_count = len(self.contract_repository.find_by_partner_name(contract_dto.partner_name)) + 1
        contract.subject = contract_dto.subject
        contract.contract_no = "C/" + str(partner_contracts_count) + "/" + contract_dto.partner_name
        return self.contract_repository.save(contract)

    def accept_contract(self, contract_id: int):
        contract = self.find(contract_id)
        attachments = self.contract_attachment_repository.find_by_contract(contract)
        if all(map(lambda x: x.status == ContractAttachment.Status.ACCEPTED_BY_ONE_SIDE, attachments)):
            contract.status = Contract.Status.ACCEPTED
        else:
            raise AttributeError("Not all attachments accepted by both sides")
        self.contract_repository.save(contract)

    def reject_contract(self, contract_id):
        contract = self.find(contract_id)
        contract.status = Contract.Status.REJECTED
        self.contract_repository.save(contract)

    def reject_attachment(self, attachment_id: int) -> None:
        contract_attachment = self.contract_attachment_repository.get_one(attachment_id)
        contract_attachment.status = ContractAttachment.Status.REJECTED
        self.contract_attachment_repository.save(contract_attachment)

    def accept_attachment(self, contract_id, attachment_id):
        contract_attachment = self.contract_attachment_repository.get_one(attachment_id)
        if contract_attachment.status == ContractAttachment.Status.ACCEPTED_BY_ONE_SIDE or \
                contract_attachment.status == ContractAttachment.Status.ACCEPTED_BY_BOTH_SIDES:
            contract_attachment.status = ContractAttachment.Status.ACCEPTED_BY_BOTH_SIDES
        else:
            contract_attachment.status = ContractAttachment.Status.ACCEPTED_BY_ONE_SIDE
        self.contract_attachment_repository.save(contract_attachment)

    def find(self, contract_id: int):
        contract = self.contract_repository.get_one(contract_id)
        if contract is None:
            raise AttributeError("Contract does not exist")
        return contract

    def find_dto(self, contract_id: int):
        return ContractDTO(contract=self.find(contract_id))

    def propose_attachment(self, contract_id: int, contract_attachment_dto: ContractAttachmentDTO):
        contract = self.find(contract_id)
        contract_attachment = ContractAttachment()
        contract_attachment.contract = contract
        contract_attachment.data = contract_attachment_dto.data
        self.contract_attachment_repository.save(contract_attachment)
        contract.attachments.append(contract_attachment)
        return ContractAttachmentDTO(**contract_attachment.dict())

    def remove_attachment(self, attachment_id: int):
        # //TODO sprawdzenie czy nalezy do kontraktu (JIRA: II-14455)
        self.contract_attachment_repository.delete_by_id(attachment_id)


