from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel

from entity.claim import Claim


class ClaimDTO(BaseModel):
    id: Optional[int]
    claim_id: int = 0
    client_id: int = 0
    transit_id: int = 0
    reason: str
    incident_description: str
    is_draft: bool
    creation_date: datetime
    completion_date: datetime
    change_date: datetime
    completion_mode: Claim.CompletionMode
    status: Claim.Status
    claim_no: str

    def __init__(self, **data: Any):
        if data.get("status") == Claim.Status.DRAFT:
            data["draft"] = True
        else:
            data["draft"] = False
        super().__init__(**data)

