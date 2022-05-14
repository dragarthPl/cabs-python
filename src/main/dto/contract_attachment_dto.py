from datetime import datetime
from typing import Optional, Any

from entity import ContractAttachment
from pydantic import BaseModel


class ContractAttachmentDTO(BaseModel):
    id: Optional[int]
    contract_id: Optional[int]
    data: Optional[bytes]
    creation_date: Optional[datetime]
    accepted_at: Optional[datetime]
    rejected_at: Optional[datetime]
    change_date: Optional[datetime]
    status: Optional[ContractAttachment.Status]

    def __init__(self, **data: Any):
        super().__init__(**data)
