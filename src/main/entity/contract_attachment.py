from datetime import datetime
from enum import Enum

from src.main.common.base_entity import BaseEntity
from entity import Contract


class ContractAttachment(BaseEntity, table=True):
    class Status(Enum):
        PROPOSED = 1
        ACCEPTED_BY_ONE_SIDE = 2
        ACCEPTED_BY_BOTH_SIDES = 3
        REJECTED = 4

    data: bytes
    creation_date: datetime
    accepted_at: datetime
    rejected_at: datetime
    change_date: datetime
    status: Status = Status.PROPOSED
    contract: Contract
