import uuid as uuid_pkg
from typing import List, Optional

from sqlalchemy import text

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

    def find_by_attachment_id(self, attachment_id: int) -> Contract:
        stmt = text(
            "SELECT c.id, c.partner_name, c.subject, c.creation_date, c.accepted_at, c.rejected_at, c.change_date,"
            " c.status, c.contract_no"
            " FROM contract as c JOIN ContractAttachment AS ca ON ca.contract_id = c.id WHERE ca.id = :attachment_id")
        return self.session.query(Contract).from_statement(stmt).params(
            attachment_id=attachment_id
        ).one_or_none()

    def find_contract_attachment_no_by_id(self, attachment_id: int) -> Optional[uuid_pkg.UUID]:
        stmt = text(
            "SELECT c.contract_attachment_no FROM ContractAttachment AS c WHERE c.id = :attachment_id"
        )
        stmt = stmt.params(attachment_id=attachment_id)
        result = self.session.execute(stmt).one_or_none()
        return uuid_pkg.UUID(result[0]) if result else None

    def get_one(self, contract_id: int) -> Optional[Contract]:
        return self.session.query(Contract).filter(Contract.id == contract_id).first()
