from dto.contract_attachment_dto import ContractAttachmentDTO
from dto.contract_dto import ContractDTO
from entity import Contract, ContractAttachmentData
from fastapi import Depends

from repository.contract_attachment_data_repository import ContractAttachmentDataRepositoryImp
from repository.contract_repository import ContractRepositoryImp


class ContractService:
    contract_repository: ContractRepositoryImp
    contract_attachment_data_repository: ContractAttachmentDataRepositoryImp

    def __init__(
            self,
            contract_repository: ContractRepositoryImp = Depends(ContractRepositoryImp),
            contract_attachment_data_repository: ContractAttachmentDataRepositoryImp = Depends(
                ContractAttachmentDataRepositoryImp
            )
    ):
        self.contract_repository = contract_repository
        self.contract_attachment_data_repository = contract_attachment_data_repository

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
        contract_attachment_no = self.contract_repository.find_contract_attachment_no_by_id(attachment_id)
        contract.reject_attachment(contract_attachment_no)
        self.contract_repository.save(contract)

    def accept_attachment(self, attachment_id: int):
        contract: Contract = self.contract_repository.find_by_attachment_id(attachment_id)
        contract_attachment_no = self.contract_repository.find_contract_attachment_no_by_id(attachment_id)
        contract.accept_attachment(contract_attachment_no)
        self.contract_repository.save(contract)

    def find(self, contract_id: int):
        contract = self.contract_repository.get_one(contract_id)
        if contract is None:
            raise AttributeError("Contract does not exist")
        return contract

    def find_dto(self, contract_id: int):
        contract = self.find(contract_id)
        return ContractDTO(
            contract=contract,
            attachments=self.contract_attachment_data_repository.find_by_contract_attachment_no_in(
                contract.get_attachment_ids()
            )
        )

    def propose_attachment(self, contract_id: int, contract_attachment_dto: ContractAttachmentDTO):
        contract = self.find(contract_id)
        contract_attachment_id = contract.propose_attachment().contract_attachment_no
        contract_attachment_data = ContractAttachmentData(
            contract_attachment_id=contract_attachment_id,
            data=contract_attachment_dto.data
        )
        contract = self.contract_repository.save(contract)
        return ContractAttachmentDTO(
            attachment=contract.find_attachment(contract_attachment_id),
            data=self.contract_attachment_data_repository.save(contract_attachment_data)
        )

    def remove_attachment(self, contract_id: int, attachment_id: int):
        # //TODO sprawdzenie czy nalezy do kontraktu (JIRA: II-14455)
        contract = self.find(contract_id)
        contract_attachment_no = self.contract_repository.find_contract_attachment_no_by_id(attachment_id)
        contract.remove(contract_attachment_no)
        self.contract_attachment_data_repository.delete_by_attachment_id(attachment_id)
