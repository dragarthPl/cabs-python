from datetime import datetime
from typing import Optional, Any

from agreements.contract_attachment_status import ContractAttachmentStatus
from agreements.contract_attachment import ContractAttachment
from agreements.contract_attachment_data import ContractAttachmentData
from pydantic import BaseModel


class ContractAttachmentDTO(BaseModel):
    id: Optional[int]
    contract_id: Optional[int]
    data: Optional[bytes]
    creation_date: Optional[datetime]
    accepted_at: Optional[datetime]
    rejected_at: Optional[datetime]
    change_date: Optional[datetime]
    status: Optional[ContractAttachmentStatus]

    def __init__(self, *, attachment: ContractAttachment = None, data: ContractAttachmentData = None, **kwargs: Any):
        super().__init__(**kwargs)
        if data is not None:
            self.data = data.data
            self.creation_date = data.creation_date
        if attachment is not None:
            self.id = attachment.id
            self.contract_id = attachment.contract_id
            self.rejected_at = attachment.rejected_at
            self.accepted_at = attachment.accepted_at
            self.change_date = attachment.change_date
            self.status = attachment.status
