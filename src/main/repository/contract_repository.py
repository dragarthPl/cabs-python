from typing import List, Optional

from core.database import get_session
from entity import Contract
from fastapi import Depends
from sqlmodel import Session


class ContractRepositoryImp:
    session: Session

    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def save(self, contract: Contract) -> Optional[Contract]:
        self.session.add(contract)
        self.session.commit()
        self.session.refresh(contract)
        return contract

    def find_by_partner_name(self, partner_name: str) -> List[Contract]:
        return self.session.query(Contract).where(Contract.partner_name == partner_name).all()

    def get_one(self, contract_id: int) -> Optional[Contract]:
        return self.session.query(Contract).filter(Contract.id == contract_id).first()
