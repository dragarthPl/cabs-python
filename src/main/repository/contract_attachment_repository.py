from typing import List, Optional

from core.database import get_session
from entity import Contract, ContractAttachment
from fastapi import Depends
from sqlmodel import Session


class ContractAttachmentRepositoryImp:
    session: Session

    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def save(self, contract_attachment: ContractAttachment) -> Optional[ContractAttachment]:
        self.session.add(contract_attachment)
        self.session.commit()
        self.session.refresh(contract_attachment)
        return contract_attachment

    def get_one(self, attachment_id: int) -> Optional[ContractAttachment]:
        return self.session.query(ContractAttachment).filter(ContractAttachment.id == attachment_id).first()

    def delete_by_id(self, attachment_id: int):
        # TODO sprawdzenie czy nalezy do kontraktu (JIRA: II-14455)
        self.session.query(ContractAttachment).filter(ContractAttachment.id == attachment_id).delete()

    def find_by_contract(self, contract: Contract) -> List[ContractAttachment]:
        return self.session.query(ContractAttachment).where(ContractAttachment.contract_id == contract.id).all()
