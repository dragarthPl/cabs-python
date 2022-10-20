from datetime import datetime
from typing import Any, Optional

from crm.claims.claim import Claim
from pydantic import BaseModel

from crm.claims.status import Status


class ClaimDTO(BaseModel):
    id: Optional[int]
    claim_id: Optional[int] = 0
    client_id: Optional[int] = 0
    transit_id: Optional[int] = 0
    reason: Optional[str]
    incident_description: Optional[str]
    is_draft: Optional[bool]
    creation_date: Optional[datetime]
    completion_date: Optional[datetime]
    change_date: Optional[datetime]
    completion_mode: Optional[Claim.CompletionMode]
    status: Optional[Status]
    claim_no: Optional[str]

    def __init__(self, **data: Any):
        super().__init__(**data)
        if data.get("status") == Status.DRAFT:
            self.is_draft = True
        else:
            self.is_draft = False
