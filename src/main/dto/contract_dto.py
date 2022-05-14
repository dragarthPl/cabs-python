from datetime import datetime
from typing import List, Optional, Any, Set

from dto.contract_attachment_dto import ContractAttachmentDTO
from entity import ContractAttachment
from entity.contract import Contract
from pydantic import BaseModel


class ContractDTO(BaseModel):
    id: Optional[int]
    subject: Optional[str]
    partner_name: Optional[str]
    creation_date: Optional[datetime]
    accepted_at: Optional[datetime]
    rejected_at: Optional[datetime]
    change_date: Optional[datetime]
    status: Optional[Contract.Status]
    contract_no: Optional[str]
    attachments: List[ContractAttachmentDTO]

    def __init__(self, *, contract: Contract = None, attachments: Set[ContractAttachment] = None, **data: Any):
        if "attachments" not in data:
            data["attachments"] = []
        if contract is not None:
            data.update(**contract.dict())
        super().__init__(**data)
        if attachments:
            self.attachments = []
            for attachment in attachments:
                self.attachments.append(ContractAttachmentDTO(**attachment.dict()))
