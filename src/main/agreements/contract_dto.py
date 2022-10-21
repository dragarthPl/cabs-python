from datetime import datetime
from typing import List, Optional, Any, Set

from agreements.contract_attachment_dto import ContractAttachmentDTO
from agreements.contract_status import ContractStatus
from agreements.contract_attachment_data import ContractAttachmentData
from agreements.contract import Contract
from pydantic import BaseModel


class ContractDTO(BaseModel):
    id: Optional[int]
    subject: Optional[str]
    partner_name: Optional[str]
    creation_date: Optional[datetime]
    accepted_at: Optional[datetime]
    rejected_at: Optional[datetime]
    change_date: Optional[datetime]
    status: Optional[ContractStatus]
    contract_no: Optional[str]
    attachments: List[ContractAttachmentDTO]

    def __init__(self, *, contract: Contract = None, attachments: Set[ContractAttachmentData] = None, **data: Any):
        if "attachments" not in data:
            data["attachments"] = []
        if contract is not None:
            data.update(**contract.dict())
        super().__init__(**data)
        if attachments:
            self.attachments = []
            for attachment_data in attachments:
                contract_attachment_no = attachment_data.contract_attachment_no
                attachment = contract.find_attachment(contract_attachment_no)
                self.attachments.append(ContractAttachmentDTO(
                    attachment=attachment,
                    data=attachment_data,
                ))
