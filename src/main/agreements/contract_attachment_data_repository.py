import uuid as uuid_pkg
from typing import Optional, List, Set

from injector import inject
from sqlalchemy import text

from sqlmodel import Session

from agreements.contract_attachment_data import ContractAttachmentData


class ContractAttachmentDataRepositoryImp:
    session: Session

    @inject
    def __init__(self, session: Session):
        self.session = session

    def find_by_contract_attachment_no_in(
            self, attachment_ids: List[uuid_pkg.UUID]
    ) -> Set[ContractAttachmentData]:
        return set(self.session.query(ContractAttachmentData).where(
            ContractAttachmentData.contract_attachment_no.in_(attachment_ids)
        ).all())

    def delete_by_attachment_id(self, attachment_id: int):
        stmt = text((
            "delete FROM ContractAttachmentData AS cad WHERE cad.contract_attachment_no ="
            " (SELECT ca.contract_attachment_no FROM ContractAttachment AS ca WHERE ca.id = :attachment_id)"
        ))
        stmt = stmt.params(attachment_id=attachment_id)
        self.session.execute(stmt)

    def save(self, contract_attachment_data: ContractAttachmentData) -> Optional[ContractAttachmentData]:
        self.session.add(contract_attachment_data)
        self.session.commit()
        self.session.refresh(contract_attachment_data)
        return contract_attachment_data

