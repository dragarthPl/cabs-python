from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel

from dto.client_dto import ClientDTO
from entity.miles.awards_account import AwardsAccount


class AwardsAccountDTO(BaseModel):
    client: Optional[ClientDTO]
    date: Optional[datetime]
    is_active: Optional[bool]
    transactions: Optional[int]

    def __init__(self, *, awards_account: AwardsAccount = None, client_dto: ClientDTO = None, **data: Any):
        if awards_account is not None:
            data.update(**awards_account.dict())
        super().__init__(**data)
        if client_dto:
            self.client = client_dto
